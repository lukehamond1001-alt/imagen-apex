"""
Deploy SAM 3D Objects to Google Vertex AI

This script handles:
1. Building the Docker image with Cloud Build
2. Pushing to Artifact Registry
3. Creating the Model in Vertex AI
4. Deploying to an Endpoint with GPU
"""

import os
import sys
import argparse
import subprocess
import time

from google.cloud import aiplatform
from google.cloud.aiplatform import Model, Endpoint


# Configuration
DEFAULT_PROJECT_ID = "gen-lang-client-0680575763"
DEFAULT_REGION = "us-central1"
DEFAULT_REPO_NAME = "sam3d-repo"
DEFAULT_IMAGE_NAME = "sam3d-vertex"
DEFAULT_MODEL_NAME = "sam3d-objects"
DEFAULT_ENDPOINT_NAME = "sam3d-endpoint"

# Machine configuration for deployment
# A100 40GB recommended, V100 32GB minimum
MACHINE_TYPE = "n1-standard-8"
ACCELERATOR_TYPE = "NVIDIA_TESLA_V100"  # or "NVIDIA_TESLA_A100"
ACCELERATOR_COUNT = 1


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
        "--description=SAM 3D Objects Vertex AI containers"
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
    
    # Create cloudbuild.yaml for the build
    cloudbuild_config = f"""
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - '{image_uri}'
      - '.'
    timeout: '3600s'
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
    print("This may take 20-30 minutes...")
    
    # Submit build to Cloud Build (use global region to avoid quota issues)
    run_command([
        "gcloud", "builds", "submit",
        f"--project={project_id}",
        "--config=cloudbuild.yaml",
        "."
    ])
    
    print(f"Image built and pushed: {image_uri}")
    return image_uri


def create_model(
    project_id: str,
    region: str,
    model_name: str,
    image_uri: str,
    hf_token: str
) -> Model:
    """Create a Model resource in Vertex AI."""
    print(f"\n{'='*60}")
    print("Step 3: Creating Vertex AI Model")
    print(f"{'='*60}")
    
    aiplatform.init(project=project_id, location=region)
    
    # Check for existing model
    existing_models = Model.list(filter=f'display_name="{model_name}"')
    if existing_models:
        print(f"Model {model_name} already exists. Using existing model.")
        return existing_models[0]
    
    # Create model
    model = Model.upload(
        display_name=model_name,
        serving_container_image_uri=image_uri,
        serving_container_predict_route="/predict",
        serving_container_health_route="/health",
        serving_container_ports=[8080],
        serving_container_environment_variables={
            "HF_TOKEN": hf_token,
        },
        description="Meta SAM 3D Objects - 3D reconstruction from single images"
    )
    
    print(f"Created model: {model.display_name} ({model.resource_name})")
    return model


def deploy_model(
    project_id: str,
    region: str,
    model: Model,
    endpoint_name: str
) -> Endpoint:
    """Deploy the model to a Vertex AI Endpoint."""
    print(f"\n{'='*60}")
    print("Step 4: Deploying Model to Endpoint")
    print(f"{'='*60}")
    
    aiplatform.init(project=project_id, location=region)
    
    # Check for existing endpoint
    existing_endpoints = Endpoint.list(filter=f'display_name="{endpoint_name}"')
    if existing_endpoints:
        endpoint = existing_endpoints[0]
        print(f"Using existing endpoint: {endpoint_name}")
    else:
        # Create endpoint
        endpoint = Endpoint.create(display_name=endpoint_name)
        print(f"Created endpoint: {endpoint_name}")
    
    # Deploy model to endpoint
    print("Deploying model (this may take 10-20 minutes)...")
    
    model.deploy(
        endpoint=endpoint,
        machine_type=MACHINE_TYPE,
        accelerator_type=ACCELERATOR_TYPE,
        accelerator_count=ACCELERATOR_COUNT,
        min_replica_count=1,
        max_replica_count=1,
        traffic_percentage=100,
        deploy_request_timeout=1800,  # 30 minutes
    )
    
    print(f"Model deployed to endpoint: {endpoint.resource_name}")
    return endpoint


def undeploy_all(project_id: str, region: str, endpoint_name: str):
    """Undeploy all models from an endpoint."""
    print(f"\n{'='*60}")
    print("Undeploying all models from endpoint")
    print(f"{'='*60}")
    
    aiplatform.init(project=project_id, location=region)
    
    endpoints = Endpoint.list(filter=f'display_name="{endpoint_name}"')
    if not endpoints:
        print(f"Endpoint {endpoint_name} not found.")
        return
    
    endpoint = endpoints[0]
    
    # Get deployed models
    deployed_models = endpoint.list_models()
    for deployed_model in deployed_models:
        print(f"Undeploying model: {deployed_model.id}")
        endpoint.undeploy(deployed_model_id=deployed_model.id)
    
    print("All models undeployed.")


def main():
    parser = argparse.ArgumentParser(description="Deploy SAM 3D Objects to Vertex AI")
    parser.add_argument("--project", default=DEFAULT_PROJECT_ID, help="GCP project ID")
    parser.add_argument("--region", default=DEFAULT_REGION, help="GCP region")
    parser.add_argument("--repo", default=DEFAULT_REPO_NAME, help="Artifact Registry repo name")
    parser.add_argument("--image", default=DEFAULT_IMAGE_NAME, help="Docker image name")
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME, help="Vertex AI model name")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT_NAME, help="Vertex AI endpoint name")
    parser.add_argument("--hf-token", required=True, help="HuggingFace access token")
    parser.add_argument("--undeploy", action="store_true", help="Undeploy all models from endpoint")
    parser.add_argument("--skip-build", action="store_true", help="Skip Docker build step")
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║           SAM 3D Objects - Vertex AI Deployment          ║
╠══════════════════════════════════════════════════════════╣
║  Project:  {args.project:<45} ║
║  Region:   {args.region:<45} ║
║  Model:    {args.model:<45} ║
║  Endpoint: {args.endpoint:<45} ║
╚══════════════════════════════════════════════════════════╝
""")
    
    if args.undeploy:
        undeploy_all(args.project, args.region, args.endpoint)
        return
    
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
    
    # Step 3: Create Model
    model = create_model(
        args.project, args.region, args.model, image_uri, args.hf_token
    )
    
    # Step 4: Deploy Model
    endpoint = deploy_model(args.project, args.region, model, args.endpoint)
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                  Deployment Complete!                    ║
╠══════════════════════════════════════════════════════════╣
║  Endpoint ID: {endpoint.name:<42} ║
║                                                          ║
║  Test with:                                              ║
║    python pipeline.py --prompt "a red car"               ║
╚══════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
