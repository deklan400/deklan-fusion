#!/usr/bin/env bash
set -euo pipefail

SWAPFILE="/swapfile"

echo "[INFO] Removing active SWAP..."

swapoff -a || true

if [[ -f "$SWAPFILE" ]]; then
    rm -f "$SWAPFILE"
    echo "[OK] Deleted swapfile."
else
    echo "[WARN] No swapfile found."
fi

sed -i '/\/swapfile/d' /etc/fstab

echo "[OK] Swap removed."
free -h
