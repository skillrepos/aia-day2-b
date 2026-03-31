FROM mcr.microsoft.com/devcontainers/base:bookworm

# Install prerequisites
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        zstd curl ca-certificates python3 python3-venv python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Pre-build the Python virtual environment
# Install CPU-only PyTorch FIRST to avoid pulling in GPU/triton packages
COPY requirements/requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/py_env && \
    /opt/py_env/bin/pip install --no-cache-dir \
        torch torchvision torchaudio \
        --index-url https://download.pytorch.org/whl/cpu && \
    grep -ivE '^torch(vision|audio)?>=' /tmp/requirements.txt > /tmp/requirements_filtered.txt && \
    /opt/py_env/bin/pip install --no-cache-dir -r /tmp/requirements_filtered.txt && \
    /opt/py_env/bin/pip freeze | grep -iE '^(nvidia|cuda|triton)' \
        | cut -d= -f1 | xargs -r /opt/py_env/bin/pip uninstall -y 2>/dev/null || true && \
    find /opt/py_env -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/py_env -name "*.pyc" -delete 2>/dev/null || true

# Pre-download the sentence-transformers embedding model
RUN /opt/py_env/bin/python -c \
    "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Pre-install Ollama (binary only — no model pull)
# Remove CUDA/Vulkan GPU libraries (~4.6 GB) since Codespaces is CPU-only
RUN curl -fsSL https://ollama.com/install.sh | sh && \
    rm -rf /usr/local/lib/ollama/cuda_v12 \
           /usr/local/lib/ollama/cuda_v13 \
           /usr/local/lib/ollama/mlx_cuda_v13 \
           /usr/local/lib/ollama/vulkan
