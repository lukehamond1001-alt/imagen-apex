# Imagen Apex

Text-to-3D generation pipeline using Google Vertex AI (Nano Banana Pro) and Meta's SAM 3D Objects.

## Prerequisites

- **Python 3.11+**
- **Google Cloud Platform (GCP)** account with Vertex AI API enabled
- **HuggingFace Account** with access token (for model downloads)

## Installation

```bash
# Clone the repository
git clone https://github.com/lukehamond1001-alt/imagen-apex.git
cd imagen-apex

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

## Configuration

Edit your `.env` file with the following credentials:

| Variable | Description |
| :--- | :--- |
| `GCP_PROJECT_ID` | Your Google Cloud Project ID |
| `GCP_REGION` | Region for Vertex AI (e.g., `us-central1`) |
| `HF_TOKEN` | HuggingFace Access Token |
| `SAM3D_ENDPOINT` | URL of your deployed SAM 3D server |
| `SAM3D_API_KEY` | API Key for the SAM 3D server |

## Usage

### Command Line Interface

Generate a 3D model from a text prompt:

```bash
python -m src.pipeline --prompt "a vintage wooden treasure chest" --output output/chest.ply
```

Use an existing image as input:

```bash
python -m src.pipeline --image my_photo.jpg --output model.ply
```

### Python API

```python
from src.pipeline import TextTo3DPipeline

pipeline = TextTo3DPipeline(
    project_id="your-gcp-project",
    sam3d_endpoint="https://your-sam3d-endpoint"
)

result = pipeline.generate(
    prompt="a red sports car",
    output_path="output/car.ply"
)

print(f"Model saved to: {result['ply']}")
```

## Deployment

You can deploy the SAM 3D inference server to Google Cloud Run (GPU enabled) or Vertex AI.

**Deploy to Cloud Run (Recommended):**

```bash
python deploy/deploy_cloudrun.py \
    --project your-project-id \
    --region us-central1 \
    --hf-token $HF_TOKEN
```

**Deploy to Vertex AI:**

```bash
python deploy/deploy_vertex.py \
    --project your-project-id \
    --region us-central1 \
    --hf-token $HF_TOKEN
```
