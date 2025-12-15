"""
SAM 3D Objects - Cloud Run Prediction Handler

FastAPI server for serving SAM 3D Objects model on Cloud Run with GPU.
Accepts images and optional masks, returns 3D Gaussian splat PLY files.
Includes API key authentication.
"""

import os
import sys
import base64
import tempfile
import logging
import secrets
from io import BytesIO
from typing import Optional

import numpy as np
from PIL import Image
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Key configuration - set via environment variable or use default
API_KEY = os.environ.get("SAM3D_API_KEY", "sam3d-demo-key-2024")

# Add SAM 3D to path
sys.path.insert(0, "/app/sam3d")
sys.path.insert(0, "/app/sam3d/notebook")

# Global model instance
inference_model = None

app = FastAPI(title="SAM 3D Objects API", version="1.0.0")


class PredictionRequest(BaseModel):
    """Request body for prediction endpoint."""
    image: str  # Base64 encoded image
    mask: Optional[str] = None  # Base64 encoded mask (optional)
    seed: int = 42


class PredictionResponse(BaseModel):
    """Response body for prediction endpoint."""
    ply: str  # Base64 encoded PLY file
    status: str


class HealthResponse(BaseModel):
    """Response body for health endpoint."""
    status: str
    model_loaded: bool


def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """Verify API key from request header."""
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key. Include X-API-Key header.")
    if not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


def download_checkpoints():
    """Download model checkpoints from HuggingFace."""
    hf_token = os.environ.get("HF_TOKEN", "")
    if not hf_token:
        logger.warning("HF_TOKEN not set. Attempting to use cached credentials.")
    
    try:
        from huggingface_hub import snapshot_download
        
        checkpoint_dir = "/app/sam3d/checkpoints/hf"
        
        if not os.path.exists(checkpoint_dir) or not os.listdir(checkpoint_dir):
            logger.info("Downloading SAM 3D Objects checkpoints from HuggingFace...")
            
            # Download the entire model repository
            snapshot_download(
                repo_id="facebook/sam-3d-objects",
                local_dir="/app/sam3d/checkpoints/hf-download",
                token=hf_token if hf_token else None,
                max_workers=1
            )
            
            # Move checkpoints to expected location
            import shutil
            src = "/app/sam3d/checkpoints/hf-download/checkpoints"
            if os.path.exists(src):
                shutil.move(src, checkpoint_dir)
            else:
                # If structure is different, use download dir directly
                shutil.move("/app/sam3d/checkpoints/hf-download", checkpoint_dir)
            
            logger.info("Checkpoints downloaded successfully.")
        else:
            logger.info("Checkpoints already exist, skipping download.")
            
    except Exception as e:
        logger.error(f"Failed to download checkpoints: {e}")
        raise


def load_model():
    """Load the SAM 3D Objects model."""
    global inference_model
    
    if inference_model is not None:
        return inference_model
    
    try:
        # Download checkpoints if needed
        download_checkpoints()
        
        # Import inference module
        from inference import Inference
        
        # Load model
        config_path = "/app/sam3d/checkpoints/hf/pipeline.yaml"
        logger.info(f"Loading model from {config_path}")
        
        inference_model = Inference(config_path, compile=False)
        logger.info("Model loaded successfully!")
        
        return inference_model
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


def decode_image(base64_string: str) -> Image.Image:
    """Decode a base64 string to a PIL Image."""
    try:
        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
        return image.convert("RGB")
    except Exception as e:
        raise ValueError(f"Failed to decode image: {e}")


def decode_mask(base64_string: str) -> np.ndarray:
    """Decode a base64 string to a numpy mask array."""
    try:
        mask_data = base64.b64decode(base64_string)
        mask_image = Image.open(BytesIO(mask_data))
        return np.array(mask_image.convert("L"))
    except Exception as e:
        raise ValueError(f"Failed to decode mask: {e}")


def encode_ply(ply_path: str) -> str:
    """Encode a PLY file to base64."""
    with open(ply_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    logger.info("Starting SAM 3D Objects server...")
    logger.info(f"API Key configured: {'Yes (from env)' if os.environ.get('SAM3D_API_KEY') else 'Using default'}")
    try:
        load_model()
    except Exception as e:
        logger.error(f"Failed to load model on startup: {e}")
        # Don't raise - allow health check to report model not loaded


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint (no auth required for Cloud Run)."""
    return HealthResponse(
        status="healthy",
        model_loaded=inference_model is not None
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "SAM 3D Objects API", "version": "1.0.0", "auth": "API key required"}


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest, api_key: str = Depends(verify_api_key)):
    """
    Generate 3D model from image and optional mask.
    Requires API key in X-API-Key header.
    
    Args:
        request: PredictionRequest with base64 image and optional mask
        
    Returns:
        PredictionResponse with base64 encoded PLY file
    """
    global inference_model
    
    if inference_model is None:
        try:
            load_model()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Model not loaded: {e}")
    
    try:
        # Decode image
        image = decode_image(request.image)
        logger.info(f"Received image: {image.size}")
        
        # Handle mask
        if request.mask:
            mask = decode_mask(request.mask)
            logger.info(f"Received mask: {mask.shape}")
        else:
            # Create full-image mask if none provided
            mask = np.ones((image.height, image.width), dtype=np.uint8) * 255
            logger.info("Using full-image mask")
        
        # Run inference
        logger.info("Running SAM 3D inference...")
        output = inference_model(image, mask, seed=request.seed)
        
        # Save PLY to temp file
        with tempfile.NamedTemporaryFile(suffix=".ply", delete=False) as f:
            ply_path = f.name
        
        output["gs"].save_ply(ply_path)
        logger.info(f"Saved PLY to {ply_path}")
        
        # Encode and return
        ply_base64 = encode_ply(ply_path)
        
        # Clean up temp file
        os.unlink(ply_path)
        
        return PredictionResponse(
            ply=ply_base64,
            status="success"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
