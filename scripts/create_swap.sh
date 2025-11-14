#!/usr/bin/env bash
set -euo pipefail

SIZE="$1"   # contoh 32, 50, 80, 100
SWAPFILE="/swapfile"

echo "[INFO] Creating SWAP ${SIZE}G..."

# Disable if exists
if swapon --show | grep -q "$SWAPFILE"; then
    echo "[INFO] Removing existing swap..."
    swapoff -a || true
    rm -f "$SWAPFILE"
fi

# Create new swap
echo "[INFO] Allocating ${SIZE}G..."
fallocate -l "${SIZE}G" "$SWAPFILE" || {
    echo "[WARN] fallocate failed, using dd..."
    dd if=/dev/zero of="$SWAPFILE" bs=1G count="$SIZE" status=progress
}

chmod 600 "$SWAPFILE"
mkswap "$SWAPFILE"
swapon "$SWAPFILE"

# Persist
sed -i '/\/swapfile/d' /etc/fstab
echo "$SWAPFILE none swap sw 0 0" >> /etc/fstab

echo "[OK] Swap ${SIZE}G created successfully."
swapon --show
