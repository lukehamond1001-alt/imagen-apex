"""
SAM 3D Objects API Client

Client for interacting with SAM 3D Objects endpoints on Vertex AI or Cloud Run.
"""

import base64
import time
from io import BytesIO
from typing import Optional, Dict, Any

import requests
from PIL import Image
import numpy as np

from .utils import (
    encode_image_to_base64,
    save_base64_to_file,
    create_elliptical_mask,
    get_env_or_default
)


class SAM3DClient:
    """
    Client for SAM 3D Objects API.
    
    Supports both direct HTTP endpoints (Cloud Run/GCE) and Vertex AI endpoints.
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        region: str = "asia-east1",
        timeout: int = 600,
        max_retries: int = 3
    ):
        """
        Initialize the SAM 3D client.
        
        Args:
            endpoint: SAM 3D endpoint URL or Vertex AI endpoint name
            api_key: API key for authentication (HTTP endpoints only)
            project_id: Google Cloud project ID (Vertex AI only)
            region: Google Cloud region (Vertex AI only)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.endpoint = endpoint or get_env_or_default(
            "SAM3D_ENDPOINT", 
            "http://localhost:8080/predict"
        )
        self.api_key = api_key or get_env_or_default(
            "SAM3D_API_KEY", 
            ""
        )
        self.project_id = project_id or get_env_or_default(
            "GCP_PROJECT_ID",
            ""
        )
        self.region = region
        self.timeout = timeout
        self.max_retries = max_retries
    
    def _is_http_endpoint(self) -> bool:
        """Check if endpoint is a direct HTTP URL."""
        return self.endpoint.startswith("http")
    
    def _call_http_endpoint(
        self, 
        payload: Dict[str, Any]
    ) -> str:
        """
        Call a direct HTTP endpoint (Cloud Run/GCE).
        
        Args:
            payload: Request payload with image, mask, and seed
            
        Returns:
            Base64 encoded PLY file
        """
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                print(f"   Sending request (attempt {attempt + 1}/{self.max_retries})...")
                response = requests.post(
                    self.endpoint, 
                    json=payload, 
                    headers=headers, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                if "ply" in result:
                    return result["ply"]
                else:
                    raise RuntimeError(f"Unexpected response: {result.keys()}")
                    
            except requests.RequestException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"   ⚠️ Request failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
        
        raise RuntimeError(f"API request failed after {self.max_retries} attempts: {last_error}")
    
    def _call_vertex_endpoint(
        self, 
        payload: Dict[str, Any]
    ) -> str:
        """
        Call a Vertex AI endpoint.
        
        Args:
            payload: Request payload with image, mask, and seed
            
        Returns:
            Base64 encoded PLY file
        """
        from google.cloud import aiplatform
        from google.cloud.aiplatform import Endpoint
        
        aiplatform.init(project=self.project_id, location=self.region)
        
        # Find the endpoint by name
        endpoints = Endpoint.list(filter=f'display_name="{self.endpoint}"')
        if not endpoints:
            raise RuntimeError(
                f"Endpoint '{self.endpoint}' not found. Please deploy the model first."
            )
        
        endpoint = endpoints[0]
        print(f"   Using Vertex AI endpoint: {endpoint.resource_name}")
        
        # Call the endpoint
        response = endpoint.predict(instances=[payload])
        
        if response.predictions:
            prediction = response.predictions[0]
            if isinstance(prediction, dict) and "ply" in prediction:
                return prediction["ply"]
            elif isinstance(prediction, str):
                return prediction
        
        raise RuntimeError(f"Unexpected response format: {response}")
    
    def generate_3d(
        self,
        image_path: str,
        output_path: str,
        mask_path: Optional[str] = None,
        seed: int = 42,
        resize_to: tuple = (256, 256)
    ) -> str:
        """
        Generate a 3D model from an image.
        
        Args:
            image_path: Path to the input image
            output_path: Path to save the output PLY file
            mask_path: Optional path to mask image (auto-generated if not provided)
            seed: Random seed for reproducibility
            resize_to: Size to resize image before processing
            
        Returns:
            Path to the saved PLY file
        """
        print("🔮 Generating 3D model with SAM 3D...")
        
        # Load and resize image
        img = Image.open(image_path).convert("RGB")
        img_resized = img.resize(resize_to, Image.Resampling.LANCZOS)
        
        # Encode image to base64
        buffer = BytesIO()
        img_resized.save(buffer, format="PNG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        # Create or load mask
        if mask_path:
            with open(mask_path, "rb") as f:
                mask_base64 = base64.b64encode(f.read()).decode("utf-8")
        else:
            # Auto-generate elliptical mask
            mask_array = create_elliptical_mask(resize_to[0], resize_to[1])
            mask_image = Image.fromarray(mask_array)
            mask_buffer = BytesIO()
            mask_image.save(mask_buffer, format="PNG")
            mask_base64 = base64.b64encode(mask_buffer.getvalue()).decode("utf-8")
        
        # Prepare payload
        payload = {
            "image": image_base64,
            "mask": mask_base64,
            "seed": seed
        }
        
        # Call the appropriate endpoint
        print("   Calling SAM 3D endpoint (this may take 30-60 seconds)...")
        
        if self._is_http_endpoint():
            ply_base64 = self._call_http_endpoint(payload)
        else:
            ply_base64 = self._call_vertex_endpoint(payload)
        
        # Save PLY file
        save_base64_to_file(ply_base64, output_path)
        print(f"   ✅ 3D model saved: {output_path}")
        
        return output_path
    
    def health_check(self) -> bool:
        """
        Check if the SAM 3D endpoint is healthy.
        
        Returns:
            True if endpoint is healthy
        """
        if not self._is_http_endpoint():
            return True  # Vertex AI endpoints don't have health checks
        
        try:
            health_url = self.endpoint.replace("/predict", "/health")
            response = requests.get(health_url, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False
