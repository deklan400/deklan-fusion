#!/bin/bash
set -euo pipefail

# =========================================================
# Create Swap File Script
# Usage: create_swap.sh <SIZE> (e.g., 32G, 50G, 80G, 100G)
# =========================================================

SWAP_SIZE="${1:-}"

if [ -z "$SWAP_SIZE" ]; then
    echo "❌ Usage: $0 <SIZE> (e.g., 32G, 50G, 80G, 100G)"
    exit 1
fi

# Validate format
if [[ ! "$SWAP_SIZE" =~ ^[0-9]+[GgMm]$ ]]; then
    echo "❌ Invalid size format. Use number + G or M (e.g., 32G, 8192M)"
    exit 1
fi

SWAPFILE="/swapfile"

echo "💾 Creating swap file ($SWAP_SIZE)..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root"
    exit 1
fi

# Disable existing swap
if swapon --show | grep -q "swap"; then
    echo "🔄 Disabling existing swap..."
    swapoff -a || true
fi

# Remove old swapfile if exists
if [ -f "$SWAPFILE" ]; then
    echo "🗑 Removing old swapfile..."
    rm -f "$SWAPFILE"
fi

# Create swapfile
echo "📝 Creating swapfile ($SWAP_SIZE)..."
if ! fallocate -l "$SWAP_SIZE" "$SWAPFILE" 2>/dev/null; then
    echo "⚠️ fallocate failed, using dd..."
    if [[ "$SWAP_SIZE" =~ ^([0-9]+)[Gg]$ ]]; then
        COUNT="${BASH_REMATCH[1]}"
        dd if=/dev/zero of="$SWAPFILE" bs=1G count="$COUNT" status=progress
    elif [[ "$SWAP_SIZE" =~ ^([0-9]+)[Mm]$ ]]; then
        COUNT="${BASH_REMATCH[1]}"
        dd if=/dev/zero of="$SWAPFILE" bs=1M count="$COUNT" status=progress
    else
        echo "❌ Invalid size format"
        exit 1
    fi
fi

# Set permissions
chmod 600 "$SWAPFILE"

# Format as swap
echo "🔧 Formatting swapfile..."
mkswap "$SWAPFILE"

# Enable swap
echo "✅ Enabling swap..."
swapon "$SWAPFILE"

# Add to fstab if not exists
if ! grep -q "^${SWAPFILE}" /etc/fstab; then
    echo "📝 Adding to /etc/fstab..."
    echo "${SWAPFILE} none swap sw 0 0" >> /etc/fstab
else
    echo "📝 Updating /etc/fstab..."
    sed -i "s|^${SWAPFILE}.*|${SWAPFILE} none swap sw 0 0|" /etc/fstab
fi

echo "✅ Swap file created successfully!"
echo "📊 Current swap status:"
swapon --show
free -h

