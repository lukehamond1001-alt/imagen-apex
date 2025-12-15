# SAM 3D Objects - Cloud Run Serving Container with GPU
# Optimized for Cloud Run with GPU support and pre-downloaded model weights

FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    git \
    curl \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Miniconda
ENV CONDA_DIR=/opt/conda
RUN wget -q https://repo.anaconda.com/miniconda/Miniconda3-py311_24.1.2-0-Linux-x86_64.sh -O miniconda.sh && \
    bash miniconda.sh -b -p $CONDA_DIR && \
    rm miniconda.sh
ENV PATH=$CONDA_DIR/bin:$PATH

# Create conda environment with Python 3.11
RUN conda create -n sam3d python=3.11 -y
SHELL ["conda", "run", "-n", "sam3d", "/bin/bash", "-c"]

# Set up PyTorch with CUDA 12.1
RUN pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

# Clone SAM 3D Objects repository
WORKDIR /app
RUN git clone https://github.com/facebookresearch/sam-3d-objects.git sam3d
WORKDIR /app/sam3d

# Set environment for pip installations
ENV PIP_EXTRA_INDEX_URL="https://pypi.ngc.nvidia.com https://download.pytorch.org/whl/cu121"
ENV PIP_FIND_LINKS="https://nvidia-kaolin.s3.us-east-2.amazonaws.com/torch-2.5.1_cu121.html"

# Remove nvidia-pyindex from requirements (it fails to build and is not essential)
RUN sed -i '/nvidia-pyindex/d' requirements.txt

# Install sam3d-objects base package first (without optional deps)
RUN pip install -e . --prefer-binary

# Install dev dependencies manually (excluding problematic packages)
RUN pip install pytest findpydeps pipdeptree lovely_tensors --prefer-binary || true

# Install pytorch3d dependencies
RUN pip install -e '.[p3d]' --prefer-binary || true

# Install inference dependencies
RUN pip install -e '.[inference]' --prefer-binary || true

# Apply patches as per official setup
RUN chmod +x ./patching/hydra && ./patching/hydra || true

# Install additional dependencies for serving
RUN pip install \
    fastapi \
    uvicorn \
    python-multipart \
    huggingface_hub

# ============================================
# PRE-DOWNLOAD MODEL WEIGHTS (Critical for Cloud Run)
# This avoids timeout issues during cold start
# ============================================
ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}

# Install huggingface CLI and download checkpoints at build time
RUN pip install 'huggingface-hub[cli]<1.0'

# Download SAM 3D checkpoints during build
RUN if [ -n "$HF_TOKEN" ]; then \
    huggingface-cli login --token $HF_TOKEN && \
    huggingface-cli download \
    --repo-type model \
    --local-dir /app/sam3d/checkpoints/hf-download \
    facebook/sam-3d-objects && \
    mv /app/sam3d/checkpoints/hf-download/checkpoints /app/sam3d/checkpoints/hf && \
    rm -rf /app/sam3d/checkpoints/hf-download; \
    else \
    echo "WARNING: HF_TOKEN not provided. Model will be downloaded at runtime."; \
    fi

# Copy the prediction handler
WORKDIR /app
COPY handler.py /app/handler.py

# Create checkpoints directory if not exists
RUN mkdir -p /app/sam3d/checkpoints

# Set up entrypoint
ENV PORT=8080
EXPOSE 8080

# Default API key (should be overridden via environment variable)
ENV SAM3D_API_KEY="sam3d-demo-key-2024"

# Activate conda environment and run the server
CMD ["conda", "run", "--no-capture-output", "-n", "sam3d", "python", "/app/handler.py"]
