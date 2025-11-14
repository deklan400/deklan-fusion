import os
import subprocess
import psutil
import shutil
from telegram import Update
from telegram.ext import ContextTypes

from .config import (
    SERVICE_NAME,
    RL_DIR,
    KEY_DIR,
    NODE_NAME,
    ALLOWED_USER_IDS,
)
from .keyboard import main_menu, swap_menu_kb, tools_menu_kb, settings_menu_kb
from .utils import run_cmd, human_size, save_swap_history, log_error


# ======================================================
# AUTH CHECK
# ======================================================
def is_allowed(user_id: int) -> bool:
    if not ALLOWED_USER_IDS:
        return True
    return str(user_id) in ALLOWED_USER_IDS


# ======================================================
# STATUS NODE
# ======================================================
async def status_node(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    disk = shutil.disk_usage("/")

    text = f"""
🟢 <b>{NODE_NAME} — Node Status</b>

🧠 CPU Load: <code>{cpu}%</code>
💾 RAM Used: <code>{ram.percent}%</code>
📦 Disk Used: <code>{round((disk.used/disk.total)*100, 1)}%</code>

🔧 RL_DIR: <code>{RL_DIR}</code>
🗝 KEY_DIR: <code>{KEY_DIR}</code>

Service: <b>{SERVICE_NAME}</b>
"""

    await update.callback_query.edit_message_text(text, reply_markup=main_menu(), parse_mode="HTML")


# ======================================================
# RESTART NODE
# ======================================================
async def restart_node(update: Update, context: ContextTypes.DEFAULT_TYPE):
    run_cmd(f"systemctl restart {SERVICE_NAME}")
    await update.callback_query.edit_message_text(
        f"🔄 Node <b>{NODE_NAME}</b> restarted!", parse_mode="HTML", reply_markup=main_menu()
    )


# ======================================================
# CLEAN VPS
# ======================================================
async def clean_vps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmds = [
        "sync",
        "echo 3 > /proc/sys/vm/drop_caches",
        "docker system prune -af --volumes",
        "apt autoremove -y",
        "apt clean",
        "rm -rf /var/log/*",
        "journalctl --vacuum-size=10M",
        "rm -rf /tmp/* /var/tmp/*",
        "rm -rf ~/.cache/*",
    ]

    for c in cmds:
        run_cmd(c)

    await update.callback_query.edit_message_text(
        "🧹 VPS cleaned successfully!", reply_markup=main_menu()
    )


# ======================================================
# SWAP CREATION
# ======================================================
SWAP_SIZES = {
    "swap_32": "32G",
    "swap_50": "50G",
    "swap_80": "80G",
    "swap_100": "100G",
    "swap_150": "150G",
    "swap_200": "200G",
}


async def swap_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    size = SWAP_SIZES.get(key)
    if not size:
        return

    # remove old swap
    run_cmd("swapoff -a || true")
    run_cmd("rm -f /swapfile || true")

    # create new swap
    run_cmd(f"fallocate -l {size} /swapfile || dd if=/dev/zero of=/swapfile bs=1G count={int(size.replace('G',''))}")
    run_cmd("chmod 600 /swapfile")
    run_cmd("mkswap /swapfile")
    run_cmd("swapon /swapfile")

    # persist
    run_cmd("sed -i '/swapfile/d' /etc/fstab")
    run_cmd("echo '/swapfile none swap sw 0 0' >> /etc/fstab")

    save_swap_history(size)

    await update.callback_query.edit_message_text(
        f"💾 Swap {size} created successfully!", reply_markup=swap_menu_kb()
    )


# ======================================================
# REMOVE SWAP
# ======================================================
async def swap_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    run_cmd("swapoff -a || true")
    run_cmd("rm -f /swapfile || true")
    run_cmd("sed -i '/swapfile/d' /etc/fstab")

    await update.callback_query.edit_message_text(
        "❌ Swap removed successfully!", reply_markup=swap_menu_kb()
    )


# ======================================================
# INSTALL NODE (Gensyn)
# ======================================================
async def install_node(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = (
        "bash <(curl -s https://raw.githubusercontent.com/gensyn-ai/rl-swarm/main/systemd.sh)"
    )
    run_cmd(cmd)

    await update.callback_query.edit_message_text(
        "📦 Node installation started…", reply_markup=main_menu()
    )


# ======================================================
# UPLOAD KEYS
# ======================================================
async def handle_uploaded_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    filename = update.message.document.file_name

    if filename not in ["swarm.pem", "userApiKey.json", "userData.json"]:
        await update.message.reply_text("❌ Invalid file. Upload: swarm.pem, userApiKey.json, userData.json")
        return

    save_path = os.path.join(KEY_DIR, filename)
    await file.download_to_drive(save_path)

    await update.message.reply_text(f"🗝 {filename} saved!", reply_markup=main_menu())


# ======================================================
# MONITOR NOW (Manual)
# ======================================================
async def monitor_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_file = f"{RL_DIR}/logs/swarm_launcher.log"

    if not os.path.exists(log_file):
        await update.callback_query.edit_message_text("⚠️ Log not found.", reply_markup=main_menu())
        return

    tail = run_cmd(f"tail -n 40 {log_file}")

    await update.callback_query.edit_message_text(
        f"📊 <b>Recent Logs</b>\n\n<code>{tail}</code>",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# ======================================================
# TOOLS
# ======================================================
async def tools_handler(update: Update, context, key):
    if key == "tools_logs":
        logs = run_cmd("journalctl -u rl-swarm -n 40 --no-pager")
        await update.callback_query.edit_message_text(
            f"📄 <b>Latest Logs</b>\n\n<code>{logs}</code>",
            parse_mode="HTML",
            reply_markup=tools_menu_kb(),
        )

    elif key == "tools_stop":
        run_cmd(f"systemctl stop {SERVICE_NAME}")
        await update.callback_query.edit_message_text("🛑 Node stopped.", reply_markup=tools_menu_kb())

    elif key == "tools_kill_py":
        run_cmd("pkill -9 python || true")
        await update.callback_query.edit_message_text("💀 Python killed.", reply_markup=tools_menu_kb())

    elif key == "tools_fix_docker":
        run_cmd("systemctl restart docker")
        await update.callback_query.edit_message_text("🐳 Docker restarted.", reply_markup=tools_menu_kb())

    elif key == "tools_delete_swarm":
        run_cmd("rm -rf ~/rl-swarm")
        await update.callback_query.edit_message_text("🗑 RL-Swarm removed.", reply_markup=tools_menu_kb())


# ======================================================
# SETTINGS MENU
# ======================================================
# (Dynamic settings will be added later)
async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("⚙️ Settings menu", reply_markup=settings_menu_kb())
