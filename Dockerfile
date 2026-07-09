# FARS-OS Ubuntu Base
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 1. Install System Dependencies & OS Packages
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    curl \
    git \
    systemd \
    sudo \
    ffmpeg \
    libsm6 \
    libxext6 \
    mesa-utils \
    libgl1-mesa-glx \
    x11-apps \
    zstd \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Node.js (for Next.js Desktop Dashboard)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# 3. Install Ollama (Local 7B LLM Server)
RUN curl -fsSL https://ollama.com/install.sh | sh

# 4. Setup FARS-OS Directory Structure
WORKDIR /opt/fars-os
COPY . /opt/fars-os

# 5. Install Python Dependencies for Kernel & Simulation
RUN pip3 install --no-cache-dir -r requirements.txt || echo "Continuing without strict requirements"

# 6. Install Node Dependencies for Desktop
RUN cd desktop/website && npm install || true

# 7. Install Systemd Boot Services
COPY systemd/*.service /etc/systemd/system/
RUN systemctl enable fars-kernel.service && \
    systemctl enable fars-desktop.service && \
    systemctl enable fars-ollama.service

# Setup OS Boot Hook
CMD ["/lib/systemd/systemd"]
