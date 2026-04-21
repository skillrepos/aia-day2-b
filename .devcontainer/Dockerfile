FROM mcr.microsoft.com/devcontainers/base:bookworm

# Install prerequisites (Node from NodeSource for a current LTS; Debian's
# nodejs/npm apt packages are too old and flaky for modern tooling).
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        zstd curl ca-certificates python3 python3-venv python3-pip gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
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

# Pre-warm the npx cache for the calculator-mcp training fork used in lab 1.
# Without this, the first `npx -y github:skillrepos/calculator-mcp` in a fresh
# codespace clones the repo, installs dev deps, and runs unbuild (~30–90s).
# Runs as the `vscode` user so the cache lands in /home/vscode/.npm/_npx where
# the Codespace session will hit it. `--help` forces the install+build path
# but exits before starting a server.
RUN su vscode -c "npx -y github:skillrepos/calculator-mcp --help" >/dev/null

# Pre-install Ollama (binary only — no model pull)
# Remove CUDA/Vulkan GPU libraries (~4.6 GB) since Codespaces is CPU-only
RUN curl -fsSL https://ollama.com/install.sh | sh && \
    rm -rf /usr/local/lib/ollama/cuda_v12 \
           /usr/local/lib/ollama/cuda_v13 \
           /usr/local/lib/ollama/mlx_cuda_v13 \
           /usr/local/lib/ollama/vulkan
