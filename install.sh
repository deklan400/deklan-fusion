#!/usr/bin/env bash
set -euo pipefail

# =======================================================================
# 🔥 DEKLAN FUSION — UNIFIED INSTALLER (Bot + Node Manager)
# Version: 1.0.0
# =======================================================================

GREEN="\e[32m"; RED="\e[31m"; YELLOW="\e[33m"; CYAN="\e[36m"; NC="\e[0m"
ok(){ echo -e "${GREEN}✔ $1${NC}"; }
err(){ echo -e "${RED}✘ $1${NC}"; exit 1; }
info(){ echo -e "${CYAN}$1${NC}"; }

FUSION_DIR="/opt/deklan-fusion"
BOT_DIR="$FUSION_DIR/bot"
MONITOR_DIR="$FUSION_DIR/monitor"
SCRIPTS_DIR="$FUSION_DIR/scripts"
LOG_DIR="$FUSION_DIR/logs"
KEY_DIR="$FUSION_DIR/keys"
REPO_RAW="https://raw.githubusercontent.com/deklan400/deklan-fusion/main"

# =======================================================================
info "====================================================="
info "🔥 DEKLAN FUSION — FULL INSTALL STARTED"
info "====================================================="

[[ $EUID -ne 0 ]] && err "Run this script as ROOT!"

# =======================================================================
info "[1/8] Preparing directories…"
mkdir -p "$FUSION_DIR" "$BOT_DIR" "$MONITOR_DIR" "$SCRIPTS_DIR" "$LOG_DIR" "$KEY_DIR"
ok "Directories ready"

# =======================================================================
info "[2/8] Installing system dependencies…"
apt update -y >/dev/null
apt install -y python3 python3-venv python3-pip jq curl unzip >/dev/null
ok "Dependencies OK"

# =======================================================================
info "[3/8] Creating Python virtual environment for Bot…"
python3 -m venv "$BOT_DIR/.venv"
"$BOT_DIR/.venv/bin/pip" install --upgrade pip >/dev/null

curl -fsSL "$REPO_RAW/bot/requirements.txt" -o "$BOT_DIR/requirements.txt"
"$BOT_DIR/.venv/bin/pip" install -r "$BOT_DIR/requirements.txt" >/dev/null

ok "Bot environment ready"

# =======================================================================
info "[4/8] Downloading bot + monitor files…"

curl -fsSL "$REPO_RAW/bot/bot.py"         -o "$BOT_DIR/bot.py"
curl -fsSL "$REPO_RAW/bot/utils.py"       -o "$BOT_DIR/utils.py"
curl -fsSL "$REPO_RAW/bot/actions.py"     -o "$BOT_DIR/actions.py"
curl -fsSL "$REPO_RAW/bot/keyboard.py"    -o "$BOT_DIR/keyboard.py"
curl -fsSL "$REPO_RAW/bot/config.py"      -o "$BOT_DIR/config.py"

curl -fsSL "$REPO_RAW/monitor/monitor.py" -o "$MONITOR_DIR/monitor.py"
curl -fsSL "$REPO_RAW/monitor/parser.py"  -o "$MONITOR_DIR/parser.py"

ok "Bot + Monitor downloaded"

# =======================================================================
info "[5/8] Creating .env file…"

read -rp "🔑 BOT_TOKEN: " BOT_TOKEN
read -rp "👤 ADMIN_CHAT_ID: " ADMIN_CHAT_ID

cat > "$FUSION_DIR/.env" <<EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_CHAT_ID=$ADMIN_CHAT_ID
KEY_DIR=$KEY_DIR
FUSION_DIR=$FUSION_DIR
EOF

chmod 600 "$FUSION_DIR/.env"
ok ".env created"

# =======================================================================
info "[6/8] Installing systemd services…"

# Bot service
cat > /etc/systemd/system/deklan-bot.service <<EOF
[Unit]
Description=Deklan Fusion Bot
After=network-online.target

[Service]
Type=simple
WorkingDirectory=$BOT_DIR
EnvironmentFile=$FUSION_DIR/.env
ExecStart=$BOT_DIR/.venv/bin/python $BOT_DIR/bot.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Monitor service + timer
cat > /etc/systemd/system/deklan-monitor.service <<EOF
[Unit]
Description=Deklan Fusion Monitor
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=$MONITOR_DIR
EnvironmentFile=$FUSION_DIR/.env
ExecStart=$BOT_DIR/.venv/bin/python $MONITOR_DIR/monitor.py

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/deklan-monitor.timer <<EOF
[Unit]
Description=Run Deklan Monitor every 2 hours

[Timer]
OnBootSec=60
OnUnitActiveSec=7200
Unit=deklan-monitor.service

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now deklan-bot
systemctl enable --now deklan-monitor.timer

ok "Systemd services installed"

# =======================================================================
info "[7/8] Preparing helper scripts…"

curl -fsSL "$REPO_RAW/scripts/create_swap.sh"  -o "$SCRIPTS_DIR/create_swap.sh"
curl -fsSL "$REPO_RAW/scripts/remove_swap.sh"  -o "$SCRIPTS_DIR/remove_swap.sh"
curl -fsSL "$REPO_RAW/scripts/clean_vps.sh"    -o "$SCRIPTS_DIR/clean_vps.sh"
curl -fsSL "$REPO_RAW/scripts/restart_node.sh" -o "$SCRIPTS_DIR/restart_node.sh"

chmod +x "$SCRIPTS_DIR"/*.sh

ok "Helper scripts added"

# =======================================================================
info "[8/8] Installation complete!"

echo -e "
${GREEN}=========================================
  ✔ DEKLAN FUSION INSTALLED SUCCESSFULLY
=========================================
Bot Logs:     journalctl -u deklan-bot -f
Monitor Logs: journalctl -u deklan-monitor -f

Upload your keys via Telegram:
  swarm.pem
  userApiKey.json
  userData.json

Bot will automatically store them in:
  $KEY_DIR

🔥 Enjoy your Fully Automated Gensyn Manager Bot!
${NC}
"
