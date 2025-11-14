#!/usr/bin/env bash
set -euo pipefail

SERVICE="gensyn"

echo "[INFO] Restarting Gensyn Node..."

systemctl daemon-reload || true

if systemctl restart "$SERVICE"; then
    echo "[OK] Node restarted."
else
    echo "[ERR] Failed restart. Checking logs:"
    systemctl status "$SERVICE" --no-pager
fi
