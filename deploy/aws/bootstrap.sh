#!/bin/bash
# PolicyRAG first-boot setup for an EC2 GPU instance (Ubuntu, NVIDIA driver preinstalled).
# Runs automatically as EC2 user data (as root). Safe to re-run by hand: sudo bash bootstrap.sh
#
# Progress:  tail -f /var/log/policyrag-bootstrap.log
# Status:    cat /var/log/policyrag-status      (starting | installing | building | ready | failed: ...)
set -Eeuo pipefail

REPO_URL="${POLICYRAG_REPO_URL:-https://github.com/tobix001-spec/policy-rag.git}"
REPO_REF="${POLICYRAG_REPO_REF:-main}"
APP_DIR=/opt/policy-rag
LOG=/var/log/policyrag-bootstrap.log
STATUS=/var/log/policyrag-status
COMPOSE="docker compose -f docker/docker-compose.yml"

exec > >(tee -a "$LOG") 2>&1
status() { echo "$1" > "$STATUS"; echo "[$(date -u +%H:%M:%S)] === $1 ==="; }
trap 'status "failed: line $LINENO (see $LOG)"' ERR
export DEBIAN_FRONTEND=noninteractive

status starting

# ---------------------------------------------------------------- 1. GPU visible to the host?
if ! nvidia-smi; then
  status "failed: no NVIDIA driver; use a GPU instance with the Deep Learning Base GPU AMI"
  exit 1
fi

status installing
apt-get update -y
apt-get install -y --no-install-recommends git curl ca-certificates gnupg

# ---------------------------------------------------------------- 2. Docker + compose plugin
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
if ! docker compose version >/dev/null 2>&1; then
  apt-get install -y docker-compose-plugin
fi
systemctl enable --now docker
usermod -aG docker ubuntu || true

# ---------------------------------------------------------------- 3. NVIDIA Container Toolkit (GPU inside containers)
if ! command -v nvidia-ctk >/dev/null 2>&1; then
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
    | gpg --dearmor --yes -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
    | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
    > /etc/apt/sources.list.d/nvidia-container-toolkit.list
  apt-get update -y
  apt-get install -y nvidia-container-toolkit
fi
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker
# fails fast here if containers cannot see the GPU
docker run --rm --gpus all ubuntu:22.04 nvidia-smi -L

# ---------------------------------------------------------------- 4. Code
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch --depth 1 origin "$REPO_REF"
  git -C "$APP_DIR" checkout -f FETCH_HEAD
else
  git clone --depth 1 --branch "$REPO_REF" "$REPO_URL" "$APP_DIR"
fi
chown -R ubuntu:ubuntu "$APP_DIR"
cd "$APP_DIR"

# ---------------------------------------------------------------- 5. Build + start
# First run: ~6.6 GB of models (qwen2.5 7b + 3b), the API image (CPU torch, bge models baked in),
# and the FAISS index build. Expect 10-20 minutes.
status building
$COMPOSE build
$COMPOSE up -d

# ---------------------------------------------------------------- 6. Wait for the API (model pull + warm-up)
for i in $(seq 1 120); do                 # up to 30 minutes
  if curl -fsS http://127.0.0.1:8000/health >/tmp/policyrag-health.json 2>/dev/null; then
    cat /tmp/policyrag-health.json; echo
    if grep -q '"status":"ok"' /tmp/policyrag-health.json; then
      status ready
      $COMPOSE ps
      exit 0
    fi
  fi
  sleep 15
done
$COMPOSE ps
$COMPOSE logs --tail 50 api || true
status "failed: API not healthy after 30 minutes (see $LOG)"
exit 1
