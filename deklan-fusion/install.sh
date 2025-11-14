#!/bin/bash
set -euo pipefail

# =========================================================
# Deklan Fusion Installation Script
# =========================================================

GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERR]${NC} $*" >&2; exit 1; }

# Parse command line arguments
BOT_TOKEN=""
ADMIN_CHAT_ID=""
ADMIN_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --token)
            BOT_TOKEN="$2"
            shift 2
            ;;
        --admin-chat-id)
            ADMIN_CHAT_ID="$2"
            shift 2
            ;;
        --admin-id)
            ADMIN_ID="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --token TOKEN           Telegram Bot Token (required)"
            echo "  --admin-chat-id ID     Admin Chat ID (required)"
            echo "  --admin-id ID          Admin ID (optional)"
            echo ""
            echo "Example:"
            echo "  sudo $0 --token 123456:ABC-DEF --admin-chat-id 123456789"
            exit 0
            ;;
        *)
            error "Unknown option: $1. Use --help for usage."
            ;;
    esac
done

# Check root
if [ "$EUID" -ne 0 ]; then
    error "Script harus dijalankan sebagai root. Gunakan: sudo $0"
fi

# Validate required parameters
if [ -z "$BOT_TOKEN" ] || [ -z "$ADMIN_CHAT_ID" ]; then
    error "Missing required parameters! Use --token and --admin-chat-id. See --help for usage."
fi

# =========================================================
# 1. Setup Directories
# =========================================================
info "Setting up directories..."
INSTALL_DIR="/opt/deklan-fusion"
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/keys"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/tmp"

success "Directories created"

# =========================================================
# 2. Install Python Dependencies
# =========================================================
info "Installing Python dependencies..."
apt-get update -y
apt-get install -y python3 python3-pip python3-venv

# Create venv
python3 -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"

# Install requirements
if [ -f "$INSTALL_DIR/bot/requirements.txt" ]; then
    pip install -r "$INSTALL_DIR/bot/requirements.txt"
else
    # Install default requirements
    pip install python-telegram-bot==20.7 paramiko python-dotenv
fi

success "Python dependencies installed"

# =========================================================
# 3. Setup .env file (optional, for backward compatibility)
# =========================================================
info "Setting up .env file (optional)..."
ENV_FILE="$INSTALL_DIR/.env"

# Create .env file with provided values (optional, since we use command line args)
    cat > "$ENV_FILE" <<EOF
# Telegram Bot Configuration
# Note: Values can also be passed via command line arguments
BOT_TOKEN=$BOT_TOKEN
ADMIN_CHAT_ID=$ADMIN_CHAT_ID
ADMIN_ID=$ADMIN_ID
EOF
success ".env file created (optional, for backward compatibility)"

# =========================================================
# 4. Setup Systemd Services
# =========================================================
info "Setting up systemd services..."

# Bot service
cat > /etc/systemd/system/fusion-bot.service <<EOF
[Unit]
Description=Deklan Fusion Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="BOT_TOKEN=$BOT_TOKEN"
Environment="ADMIN_CHAT_ID=$ADMIN_CHAT_ID"
Environment="ADMIN_ID=$ADMIN_ID"
ExecStart=$INSTALL_DIR/venv/bin/python3 -m bot.bot --token "$BOT_TOKEN" --admin-chat-id "$ADMIN_CHAT_ID" --admin-id "$ADMIN_ID"
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Monitor service
cat > /etc/systemd/system/fusion-monitor.service <<EOF
[Unit]
Description=Deklan Fusion Monitor Daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="BOT_TOKEN=$BOT_TOKEN"
Environment="ADMIN_CHAT_ID=$ADMIN_CHAT_ID"
ExecStart=$INSTALL_DIR/venv/bin/python3 -m monitor.monitor --token "$BOT_TOKEN" --admin-chat-id "$ADMIN_CHAT_ID"
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Monitor timer (every 3 hours)
cat > /etc/systemd/system/fusion-monitor.timer <<EOF
[Unit]
Description=Run Deklan Fusion Monitor every 3 hours
Requires=fusion-monitor.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=3h
AccuracySec=1min

[Install]
WantedBy=timers.target
EOF

# Reload systemd
systemctl daemon-reload

success "Systemd services created"

# =========================================================
# 5. Set Permissions
# =========================================================
info "Setting permissions..."
chown -R root:root "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/bot/bot.py" 2>/dev/null || true
chmod +x "$INSTALL_DIR/scripts/*.sh" 2>/dev/null || true

success "Permissions set"

# =========================================================
# 6. Enable Services
# =========================================================
info "Enabling services..."
systemctl enable fusion-bot.service
systemctl enable fusion-monitor.timer

success "Services enabled"

# =========================================================
# Summary
# =========================================================
echo ""
success "Installation completed!"
echo ""
info "Configuration:"
echo "  - BOT_TOKEN: ${BOT_TOKEN:0:20}..."
echo "  - ADMIN_CHAT_ID: $ADMIN_CHAT_ID"
if [ -n "$ADMIN_ID" ]; then
    echo "  - ADMIN_ID: $ADMIN_ID"
fi
echo ""
info "Next steps:"
echo "  1. Start the bot: systemctl start fusion-bot"
echo "  2. Start the monitor timer: systemctl start fusion-monitor.timer"
echo ""
info "Useful commands:"
echo "  - Check bot status: systemctl status fusion-bot"
echo "  - Check monitor: systemctl status fusion-monitor"
echo "  - View bot logs: journalctl -u fusion-bot -f"
echo "  - View monitor logs: journalctl -u fusion-monitor -f"
echo "  - Restart bot: systemctl restart fusion-bot"
echo ""
warn "Note: To update tokens, edit systemd service files or re-run install.sh with new parameters"


