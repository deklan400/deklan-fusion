#!/bin/bash
set -euo pipefail

# =========================================================
# Update Gensyn RL-Swarm Node Script
# =========================================================

echo "⚙️ Updating Gensyn RL-Swarm Node..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root"
    exit 1
fi

HOME_DIR="/root"
RL_SWARM_DIR="$HOME_DIR/rl-swarm"
EZLABS_DIR="$HOME_DIR/ezlabs"

# Step 1: Stop service
echo "🛑 Stopping rl-swarm service..."
systemctl stop rl-swarm.service 2>/dev/null || true

# Step 2: Backup keys
echo "💾 Backing up keys..."
mkdir -p "$EZLABS_DIR"

# Backup keys if they exist
if [ -f "$RL_SWARM_DIR/swarm.pem" ]; then
    cp -f "$RL_SWARM_DIR/swarm.pem" "$EZLABS_DIR/swarm.pem"
    echo "✅ Backed up swarm.pem"
fi

if [ -f "$RL_SWARM_DIR/modal-login/temp-data/userApiKey.json" ]; then
    mkdir -p "$EZLABS_DIR"
    cp -f "$RL_SWARM_DIR/modal-login/temp-data/userApiKey.json" "$EZLABS_DIR/userApiKey.json"
    echo "✅ Backed up userApiKey.json"
fi

if [ -f "$RL_SWARM_DIR/modal-login/temp-data/userData.json" ]; then
    mkdir -p "$EZLABS_DIR"
    cp -f "$RL_SWARM_DIR/modal-login/temp-data/userData.json" "$EZLABS_DIR/userData.json"
    echo "✅ Backed up userData.json"
fi

# Step 3: Clean old files
echo "🧹 Cleaning old files..."
cd "$HOME_DIR"
rm -rf rl-swarm qwen2-official.zip

# Step 4: Download latest
echo "📥 Downloading latest RL-Swarm package..."
wget -q https://github.com/ezlabsnodes/gensyn/raw/refs/heads/main/qwen2-official.zip -O qwen2-official.zip

if [ ! -f "qwen2-official.zip" ]; then
    echo "❌ Failed to download package"
    exit 1
fi

# Step 5: Extract
echo "📦 Extracting package..."
unzip -o qwen2-official.zip >/dev/null

if [ ! -d "$RL_SWARM_DIR" ]; then
    echo "❌ Extraction failed"
    exit 1
fi

# Step 6: Restore keys
echo "🔑 Restoring keys..."
if [ -f "$EZLABS_DIR/swarm.pem" ]; then
    cp -f "$EZLABS_DIR/swarm.pem" "$RL_SWARM_DIR/swarm.pem"
    echo "✅ Restored swarm.pem"
fi

if [ -f "$EZLABS_DIR/userApiKey.json" ]; then
    mkdir -p "$RL_SWARM_DIR/modal-login/temp-data"
    cp -f "$EZLABS_DIR/userApiKey.json" "$RL_SWARM_DIR/modal-login/temp-data/userApiKey.json"
    echo "✅ Restored userApiKey.json"
fi

if [ -f "$EZLABS_DIR/userData.json" ]; then
    mkdir -p "$RL_SWARM_DIR/modal-login/temp-data"
    cp -f "$EZLABS_DIR/userData.json" "$RL_SWARM_DIR/modal-login/temp-data/userData.json"
    echo "✅ Restored userData.json"
fi

# Step 7: Setup venv and permissions
echo "🔧 Setting up environment..."
cd "$RL_SWARM_DIR"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
chmod +x run_rl_swarm.sh 2>/dev/null || true

# Step 8: Restart service
echo "🔄 Restarting rl-swarm service..."
systemctl daemon-reload
systemctl start rl-swarm.service

# Step 9: Cleanup
echo "🧹 Cleaning up..."
rm -f "$HOME_DIR/qwen2-official.zip"

echo "✅ Node update completed successfully!"
echo "📊 Service status:"
systemctl status rl-swarm.service --no-pager -l || true

