# Setup Guide

Complete guide for setting up Imagen Apex on your system.

## Prerequisites

### Required
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Google Cloud Account** - [Sign up](https://cloud.google.com/)
- **HuggingFace Account** - [Sign up](https://huggingface.co/join)

### Optional
- **Docker** - For local SAM 3D server
- **NVIDIA GPU** - Required for SAM 3D inference

---

## Step 1: Google Cloud Setup

### 1.1 Create a Project

```bash
# Install gcloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

# Login to Google Cloud
gcloud auth login

# Create a new project (or use existing)
gcloud projects create your-project-id

# Set the project
gcloud config set project your-project-id

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### 1.2 Set Up Application Default Credentials

```bash
gcloud auth application-default login
```

### 1.3 Request GPU Quota (if deploying SAM 3D)

1. Go to [IAM & Admin > Quotas](https://console.cloud.google.com/iam-admin/quotas)
2. Filter for "GPU"
3. Request quota increase for:
   - `NVIDIA L4 GPUs` (recommended, ~$0.75/hour)
   - or `NVIDIA V100 GPUs` (~$2.50/hour)

---

## Step 2: HuggingFace Setup

### 2.1 Create Access Token

1. Go to [HuggingFace Settings > Tokens](https://huggingface.co/settings/tokens)
2. Click "New token"
3. Name it "imagen-apex"
4. Set access to "Read"
5. Copy the token

### 2.2 Request Model Access

1. Go to [facebook/sam-3d-objects](https://huggingface.co/facebook/sam-3d-objects)
2. Click "Request access"
3. Accept the terms
4. Wait for approval (usually instant)

---

## Step 3: Install Imagen Apex

### 3.1 Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/imagen-apex.git
cd imagen-apex
```

### 3.2 Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3.3 Install Dependencies

```bash
pip install -r requirements.txt

# For development
pip install -e ".[dev]"
```

### 3.4 Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
HF_TOKEN=hf_xxxxxxxxxxxx
SAM3D_ENDPOINT=http://localhost:8080/predict
SAM3D_API_KEY=your-api-key
```

---

## Step 4: Deploy SAM 3D Server

You have three options for running the SAM 3D server:

### Option A: Cloud Run (Recommended)

```bash
# Set your HuggingFace token
export HF_TOKEN=hf_xxxxxxxxxxxx

# Deploy to Cloud Run
python deploy/deploy_cloudrun.py \
    --project your-project-id \
    --region us-central1 \
    --hf-token $HF_TOKEN

# The script will output your endpoint URL
# Update .env with this URL
```

### Option B: Vertex AI Endpoint

```bash
python deploy/deploy_vertex.py \
    --project your-project-id \
    --region asia-east1 \
    --hf-token $HF_TOKEN
```

### Option C: Local Docker (Requires NVIDIA GPU)

```bash
cd server

# Build the image
docker build -t imagen-apex-sam3d \
    --build-arg HF_TOKEN=$HF_TOKEN .

# Run the container
docker run --gpus all -p 8080:8080 imagen-apex-sam3d
```

---

## Step 5: Verify Installation

### Test Image Generation

```bash
python -m src.image_generator \
    --prompt "a red apple" \
    --output test_apple.png
```

### Test Full Pipeline

```bash
python -m src.pipeline \
    --prompt "a wooden chair" \
    --output test_chair.ply
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'src'"

Make sure you're in the project directory and have activated the virtual environment:

```bash
cd imagen-apex
source venv/bin/activate
```

### "Permission denied" errors with gcloud

Re-authenticate:

```bash
gcloud auth login
gcloud auth application-default login
```

### "GPU quota exceeded"

Request GPU quota increase in the GCP Console, or try a different region.

### "Model server never became ready"

1. Verify HuggingFace token is valid
2. Ensure you have SAM 3D model access
3. Check Cloud Build/Run logs for errors

---

## Next Steps

- Try the [examples](../examples/) for more usage patterns
- Read the [API documentation](API.md) for programmatic usage
- Check [Troubleshooting](TROUBLESHOOTING.md) for common issues
