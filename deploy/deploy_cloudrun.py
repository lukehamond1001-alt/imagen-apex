"""
Deploy SAM 3D Objects to Google Cloud Run with GPU

This script handles:
1. Building the Docker image with Cloud Build (including model weights)
2. Pushing to Artifact Registry
3. Deploying to Cloud Run with GPU and API key authentication
"""

import os
import sys
import argparse
import subprocess
import secrets
import string


# Configuration
DEFAULT_PROJECT_ID = "gen-lang-client-0680575763"
DEFAULT_REGION = "us-central1"
DEFAULT_REPO_NAME = "sam3d-repo"
DEFAULT_IMAGE_NAME = "sam3d-cloudrun"
DEFAULT_SERVICE_NAME = "sam3d-api"


def generate_api_key(length: int = 32) -> str:
    """Generate a secure random API key."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result


def create_artifact_registry(project_id: str, region: str, repo_name: str):
    """Create Artifact Registry repository if it doesn't exist."""
    print(f"\n{'='*60}")
    print("Step 1: Creating Artifact Registry repository")
    print(f"{'='*60}")
    
    # Check if repo exists
    result = run_command([
        "gcloud", "artifacts", "repositories", "describe",
        repo_name,
        f"--project={project_id}",
        f"--location={region}",
        "--format=value(name)"
    ], check=False)
    
    if result.returncode == 0:
        print(f"Repository {repo_name} already exists.")
        return
    
    # Create repository
    run_command([
        "gcloud", "artifacts", "repositories", "create",
        repo_name,
        f"--project={project_id}",
        f"--location={region}",
        "--repository-format=docker",
        "--description=SAM 3D Objects Cloud Run containers"
    ])
    print(f"Created repository: {repo_name}")


def build_and_push_image(
    project_id: str,
    region: str,
    repo_name: str,
    image_name: str,
    hf_token: str
):
    """Build Docker image with Cloud Build and push to Artifact Registry."""
    print(f"\n{'='*60}")
    print("Step 2: Building and pushing Docker image")
    print(f"{'='*60}")
    
    image_uri = f"{region}-docker.pkg.dev/{project_id}/{repo_name}/{image_name}:latest"
    
    # Create cloudbuild.yaml for the build with HF_TOKEN as build arg
    cloudbuild_config = f"""
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '--build-arg'
      - 'HF_TOKEN={hf_token}'
      - '-t'
      - '{image_uri}'
      - '.'
    timeout: '7200s'
images:
  - '{image_uri}'
timeout: '7200s'
options:
  machineType: 'E2_HIGHCPU_32'
  diskSizeGb: 200
"""
    
    with open("cloudbuild.yaml", "w") as f:
        f.write(cloudbuild_config)
    
    print(f"Building image: {image_uri}")
    print("This may take 30-60 minutes (including model download)...")
    
    # Submit build to Cloud Build (global region)
    run_command([
        "gcloud", "builds", "submit",
        f"--project={project_id}",
        "--config=cloudbuild.yaml",
        "."
    ])
    
    print(f"Image built and pushed: {image_uri}")
    return image_uri


def deploy_to_cloud_run(
    project_id: str,
    region: str,
    service_name: str,
    image_uri: str,
    api_key: str,
    min_instances: int = 1
):
    """Deploy the container to Cloud Run with GPU."""
    print(f"\n{'='*60}")
    print("Step 3: Deploying to Cloud Run with GPU")
    print(f"{'='*60}")
    
    print(f"Deploying service: {service_name}")
    print(f"Min instances: {min_instances} (for fast demo response)")
    
    # Deploy to Cloud Run with GPU
    run_command([
        "gcloud", "run", "deploy", service_name,
        f"--project={project_id}",
        f"--region={region}",
        f"--image={image_uri}",
        "--platform=managed",
        "--gpu=1",
        "--gpu-type=nvidia-l4",
        "--cpu=8",
        "--memory=32Gi",
        f"--min-instances={min_instances}",
        "--max-instances=3",
        "--timeout=300",
        "--concurrency=1",  # One request at a time per instance (GPU inference)
        f"--set-env-vars=SAM3D_API_KEY={api_key}",
        "--allow-unauthenticated",  # We use API key auth in the app
        "--no-cpu-throttling",
    ])
    
    # Get the service URL
    result = run_command([
        "gcloud", "run", "services", "describe", service_name,
        f"--project={project_id}",
        f"--region={region}",
        "--format=value(status.url)"
    ])
    
    service_url = result.stdout.strip()
    print(f"Service deployed: {service_url}")
    return service_url


def main():
    parser = argparse.ArgumentParser(description="Deploy SAM 3D Objects to Cloud Run with GPU")
    parser.add_argument("--project", default=DEFAULT_PROJECT_ID, help="GCP project ID")
    parser.add_argument("--region", default=DEFAULT_REGION, help="GCP region")
    parser.add_argument("--repo", default=DEFAULT_REPO_NAME, help="Artifact Registry repo name")
    parser.add_argument("--image", default=DEFAULT_IMAGE_NAME, help="Docker image name")
    parser.add_argument("--service", default=DEFAULT_SERVICE_NAME, help="Cloud Run service name")
    parser.add_argument("--hf-token", required=True, help="HuggingFace access token")
    parser.add_argument("--api-key", help="API key for authentication (auto-generated if not provided)")
    parser.add_argument("--min-instances", type=int, default=1, help="Minimum instances (1 for fast demo, 0 for cost savings)")
    parser.add_argument("--skip-build", action="store_true", help="Skip Docker build step")
    
    args = parser.parse_args()
    
    # Generate or use provided API key
    api_key = args.api_key or generate_api_key()
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║      SAM 3D Objects - Cloud Run GPU Deployment           ║
╠══════════════════════════════════════════════════════════╣
║  Project:       {args.project:<40} ║
║  Region:        {args.region:<40} ║
║  Service:       {args.service:<40} ║
║  Min Instances: {args.min_instances:<40} ║
╚══════════════════════════════════════════════════════════╝
""")
    
    # Step 1: Create Artifact Registry
    create_artifact_registry(args.project, args.region, args.repo)
    
    # Step 2: Build and push Docker image
    if args.skip_build:
        image_uri = f"{args.region}-docker.pkg.dev/{args.project}/{args.repo}/{args.image}:latest"
        print(f"Skipping build. Using existing image: {image_uri}")
    else:
        image_uri = build_and_push_image(
            args.project, args.region, args.repo, args.image, args.hf_token
        )
    
    # Step 3: Deploy to Cloud Run
    service_url = deploy_to_cloud_run(
        args.project, args.region, args.service, image_uri, api_key, args.min_instances
    )
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                  Deployment Complete!                    ║
╠══════════════════════════════════════════════════════════╣

  🌐 Service URL: {service_url}
  
  🔑 API Key: {api_key}
  
  📝 Save this API key! You'll need it for all requests.

╠══════════════════════════════════════════════════════════╣
║  Usage Example:                                          ║
╚══════════════════════════════════════════════════════════╝

  curl -X POST {service_url}/predict \\
    -H "Content-Type: application/json" \\
    -H "X-API-Key: {api_key}" \\
    -d '{{"image": "<base64_image>", "seed": 42}}'

""")
    
    # Save API key to file for reference
    with open(".api_key", "w") as f:
        f.write(f"SAM3D_API_KEY={api_key}\n")
        f.write(f"SERVICE_URL={service_url}\n")
    print("API key saved to .api_key file")


if __name__ == "__main__":
    main()
