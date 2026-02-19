#!/bin/bash
# FFE Backend — EC2 Deployment Script
# Usage: bash deploy/deploy.sh
set -e

REPO_DIR="/home/ubuntu/rift"
BACKEND_DIR="$REPO_DIR/backend"
SERVICE_NAME="ffe-backend"

echo "==> Pulling latest code..."
cd "$REPO_DIR"
git pull origin main

echo "==> Installing dependencies..."
source "$BACKEND_DIR/venv/bin/activate"
pip install -r "$BACKEND_DIR/requirements.txt" -q

echo "==> Installing systemd service..."
sudo cp "$BACKEND_DIR/deploy/ffe-backend.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"

echo "==> Restarting service..."
sudo systemctl restart "$SERVICE_NAME"

echo "==> Status:"
sudo systemctl status "$SERVICE_NAME" --no-pager

echo ""
echo "Deployment complete. Check logs with:"
echo "  sudo journalctl -u $SERVICE_NAME -f"
