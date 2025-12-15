# API Reference

Complete API documentation for Imagen Apex.

---

## Core Classes

### TextTo3DPipeline

The main orchestration class for text-to-3D generation.

```python
from src.pipeline import TextTo3DPipeline

pipeline = TextTo3DPipeline(
    project_id: str = None,           # GCP project ID (uses env if not set)
    region: str = "us-central1",      # GCP region
    sam3d_endpoint: str = None,       # SAM 3D endpoint URL
    sam3d_api_key: str = None,        # SAM 3D API key
    prefer_nano_banana: bool = True   # Try Nano Banana Pro first
)
```

#### Methods

##### `generate()`

Generate a 3D model from a text prompt.

```python
results = pipeline.generate(
    prompt: str,                      # Text description
    output_path: str,                 # Path to save PLY file
    image_path: str = None,           # Optional: use existing image
    save_intermediate: bool = True,   # Save intermediate files
    seed: int = 42,                   # Random seed
    progress_callback: Callable = None  # Optional progress callback
)

# Returns:
# {
#     "image": "/path/to/generated_image.png",
#     "ply": "/path/to/model.ply"
# }
```

##### `generate_image_only()`

Generate only the image without 3D conversion.

```python
image_path = pipeline.generate_image_only(
    prompt: str,
    output_path: str,
    aspect_ratio: str = "1:1"  # Options: 1:1, 16:9, 9:16, 4:3, 3:4
)
```

---

### ImageGenerator

Standalone image generation with Nano Banana Pro or Imagen 3.

```python
from src.image_generator import ImageGenerator

generator = ImageGenerator(
    project_id: str = None,
    region: str = "us-central1",
    prefer_nano_banana: bool = True
)
```

#### Methods

##### `generate()`

```python
output_path = generator.generate(
    prompt: str,
    output_path: str,
    aspect_ratio: str = "1:1"
)
```

##### `generate_with_nano_banana()`

```python
success = generator.generate_with_nano_banana(
    prompt: str,
    output_path: str
)
# Returns True if successful, False if model not available
```

##### `generate_with_imagen()`

```python
generator.generate_with_imagen(
    prompt: str,
    output_path: str,
    aspect_ratio: str = "1:1"
)
```

---

### SAM3DClient

Client for SAM 3D Objects API.

```python
from src.sam3d_client import SAM3DClient

client = SAM3DClient(
    endpoint: str = None,        # Endpoint URL or Vertex AI name
    api_key: str = None,         # API key for HTTP endpoints
    project_id: str = None,      # GCP project ID (Vertex AI)
    region: str = "asia-east1",  # GCP region (Vertex AI)
    timeout: int = 600,          # Request timeout (seconds)
    max_retries: int = 3         # Retry attempts
)
```

#### Methods

##### `generate_3d()`

```python
ply_path = client.generate_3d(
    image_path: str,             # Input image path
    output_path: str,            # Output PLY path
    mask_path: str = None,       # Optional mask (auto-generated if None)
    seed: int = 42,              # Random seed
    resize_to: tuple = (256, 256)  # Image resize dimensions
)
```

##### `health_check()`

```python
is_healthy = client.health_check()
# Returns True if endpoint is responsive
```

---

## Utility Functions

### `src.utils`

```python
from src.utils import (
    encode_image_to_base64,
    decode_base64_to_image,
    save_base64_to_file,
    create_elliptical_mask,
    resize_image,
    get_env_or_default,
    ensure_directory
)
```

#### `encode_image_to_base64(image_path: str) -> str`

Encode an image file to base64 string.

#### `decode_base64_to_image(base64_string: str) -> PIL.Image`

Decode base64 string to PIL Image.

#### `create_elliptical_mask(width: int, height: int, coverage: float = 0.6) -> np.ndarray`

Create an elliptical mask for object segmentation.

#### `resize_image(image_path: str, size: tuple = (256, 256), output_path: str = None) -> str`

Resize an image to specified dimensions.

---

## CLI Commands

### Full Pipeline

```bash
python -m src.pipeline \
    --prompt "a red sports car" \
    --output output/car.ply \
    --project your-project-id \
    --region us-central1 \
    --endpoint http://localhost:8080/predict \
    --seed 42

# Use existing image
python -m src.pipeline \
    --image my_photo.jpg \
    --output output/model.ply

# Image generation only
python -m src.pipeline \
    --prompt "a wooden chair" \
    --output output/chair.png \
    --image-only
```

### Image Generation Only

```bash
python -m src.image_generator \
    --prompt "a golden crown" \
    --output crown.png \
    --aspect-ratio 1:1 \
    --no-nano-banana  # Skip Nano Banana Pro, use Imagen directly
```

---

## SAM 3D Server API

The SAM 3D server exposes a REST API:

### `POST /predict`

Generate 3D model from image.

**Headers:**
```
Content-Type: application/json
X-API-Key: your-api-key
```

**Request Body:**
```json
{
    "image": "<base64 encoded PNG>",
    "mask": "<base64 encoded PNG, optional>",
    "seed": 42
}
```

**Response:**
```json
{
    "ply": "<base64 encoded PLY file>",
    "status": "success"
}
```

### `GET /health`

Health check endpoint (no authentication required).

**Response:**
```json
{
    "status": "healthy",
    "model_loaded": true
}
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | Google Cloud project ID | - |
| `GCP_REGION` | Google Cloud region | `us-central1` |
| `SAM3D_ENDPOINT` | SAM 3D endpoint URL | `http://localhost:8080/predict` |
| `SAM3D_API_KEY` | SAM 3D API key | `sam3d-demo-key-2024` |
| `HF_TOKEN` | HuggingFace access token | - |
| `PREFER_NANO_BANANA` | Try Nano Banana Pro first | `true` |
