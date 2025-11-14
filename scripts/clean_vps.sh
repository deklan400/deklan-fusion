#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Cleaning VPS..."

# Clean logs
rm -rf /var/log/* 2>/dev/null || true
journalctl --vacuum-size=10M >/dev/null 2>&1 || true

# Clean Docker
docker system prune -af >/dev/null 2>&1 || true
docker volume prune -f >/dev/null 2>&1 || true

# Clean apt trash
apt autoremove -y >/dev/null 2>&1 || true
apt clean >/dev/null 2>&1 || true

# Clear temporary files
rm -rf /tmp/* /var/tmp/* 2>/dev/null || true

echo "[OK] VPS cleaned."
echo "RAM + disk should be lighter now."
