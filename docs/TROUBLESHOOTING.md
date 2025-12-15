# Troubleshooting Guide

Solutions for common issues with Imagen Apex.

---

## Installation Issues

### "ModuleNotFoundError: No module named 'vertexai'"

**Solution:** Install the Google Cloud dependencies:

```bash
pip install google-cloud-aiplatform vertexai
```

### "Could not find a version that satisfies the requirement"

**Solution:** Ensure you're using Python 3.11+:

```bash
python --version  # Should be 3.11.x or higher

# If not, install Python 3.11
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
```

---

## Authentication Issues

### "Permission denied" or "403 Forbidden"

**Cause:** GCP credentials not set up correctly.

**Solution:**

```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login

# Verify project
gcloud config set project your-project-id
```

### "Could not automatically determine credentials"

**Cause:** Application default credentials not configured.

**Solution:**

```bash
gcloud auth application-default login
```

Or set the environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

---

## Image Generation Issues

### "Nano Banana Pro not available"

**Cause:** Gemini 3 Pro with image generation may not be available in your region.

**Solution:** The system automatically falls back to Imagen 3. No action needed.

To force Imagen 3 directly:

```bash
python -m src.image_generator --prompt "..." --no-nano-banana
```

### "No images generated"

**Cause:** Prompt may have been blocked by safety filters.

**Solution:** Try a different prompt or adjust safety settings:

```python
# In image_generator.py, modify safety_filter_level
response = model.generate_images(
    prompt=prompt,
    safety_filter_level="block_only_high",  # Less restrictive
)
```

---

## SAM 3D Server Issues

### "Endpoint not found"

**Cause:** SAM 3D server hasn't been deployed.

**Solution:** Deploy the server:

```bash
# Cloud Run
python deploy/deploy_cloudrun.py --hf-token $HF_TOKEN

# Or Vertex AI
python deploy/deploy_vertex.py --hf-token $HF_TOKEN
```

### "Model server never became ready"

**Possible causes:**

1. **Invalid HuggingFace token**
   - Verify token at [HuggingFace Settings](https://huggingface.co/settings/tokens)
   - Ensure you have access to [facebook/sam-3d-objects](https://huggingface.co/facebook/sam-3d-objects)

2. **GPU quota exceeded**
   - Check your GPU quota in [GCP Console](https://console.cloud.google.com/iam-admin/quotas)
   - Request quota increase or try a different region

3. **Build failure**
   - Check Cloud Build logs:
     ```bash
     gcloud builds list --limit=5
     gcloud builds log BUILD_ID
     ```

### "Connection refused" or "timeout"

**Cause:** Server not running or not accessible.

**Solution:**

```bash
# Check if Cloud Run service is running
gcloud run services list

# Check service logs
gcloud run services logs read sam3d-server --limit=50

# Verify endpoint URL is correct
curl -X GET https://your-endpoint/health
```

### "CUDA out of memory"

**Cause:** Image too large for GPU memory.

**Solution:** Images are automatically resized to 256x256 for L4 GPUs. For higher resolution:

1. Use a larger GPU (V100 or A100)
2. Reduce image size in your code:

```python
client.generate_3d(
    image_path="...",
    output_path="...",
    resize_to=(128, 128)  # Smaller size
)
```

---

## 3D Model Issues

### "Empty or corrupted PLY file"

**Cause:** Server error during generation.

**Solution:**

1. Check server logs for errors
2. Try with a simpler prompt/image
3. Verify the image is a clear, single object

### "PLY file won't open in Blender/MeshLab"

**Cause:** File may be a Gaussian Splat PLY (not standard mesh).

**Solution:** SAM 3D outputs Gaussian Splat format. Use viewers that support it:

- [3D Viewer Online](https://3dviewer.net) (works with most PLY files)
- [SuperSplat](https://playcanvas.com/supersplat)
- Convert using specialized tools

---

## Deployment Issues

### "GPU quota exceeded"

**Solution:**

1. Request quota increase:
   - Go to [GCP Quotas](https://console.cloud.google.com/iam-admin/quotas)
   - Search for "GPU"
   - Request increase for your region

2. Try a different region:
   ```bash
   python deploy/deploy_cloudrun.py --region asia-east1
   ```

3. Use a different GPU type:
   - L4 (cheapest, ~$0.75/hour)
   - V100 (moderate, ~$2.50/hour)
   - A100 (most powerful, ~$3.50/hour)

### "Cloud Build timeout"

**Cause:** Building the Docker image takes too long.

**Solution:** Increase timeout in `cloudbuild.yaml`:

```yaml
timeout: "7200s"  # 2 hours
```

### "Image push failed"

**Cause:** Artifact Registry not set up.

**Solution:**

```bash
# Create repository
gcloud artifacts repositories create imagen-apex \
    --repository-format=docker \
    --location=us-central1

# Configure Docker auth
gcloud auth configure-docker us-central1-docker.pkg.dev
```

---

## Performance Optimization

### Slow image generation

Try these optimizations:

1. Use `us-central1` region (generally fastest)
2. Pre-warm the endpoint with a dummy request
3. Consider batch processing for multiple images

### Slow 3D generation

SAM 3D inference typically takes 30-60 seconds. To optimize:

1. Use smaller image sizes (256x256 is optimal)
2. Keep the server warm to avoid cold start
3. Consider using A100 GPUs for faster inference

---

## Getting Help

If you're still stuck:

1. Check [GitHub Issues](https://github.com/YOUR_USERNAME/imagen-apex/issues) for similar problems
2. Open a new issue with:
   - Your OS and Python version
   - Complete error message
   - Steps to reproduce
   - Relevant logs
