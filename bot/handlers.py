# deklan-fusion/bot/handlers.py

"""
Telegram Bot Handlers untuk Deklan Fusion.
"""

import os
import sys
import logging
from telegram import Update
from telegram.ext import ContextTypes

# Pastikan path lokal ke-import
sys.path.insert(0, os.path.dirname(__file__))

# Import dari package lokal
from .config import KEY_DIR, TMP_DIR  # saat ini belum dipakai, tapi keep untuk future use
from .utils import ensure_dirs
from .auth import is_admin, require_admin
from .actions import (
    add_vps, remove_vps, list_vps,
    node_status, node_start, node_restart, node_stop, node_logs,
    sync_keys_to_all_vps, vps_control_kb, get_user_vps_list, is_vps_owner
)
from .file_receiver import handle_file
from .keyboard import main_menu
from .reward_checker import check_all_rewards, load_db, check_reward
from .ssh_client import SSHClient

logger = logging.getLogger(__name__)


# ==========================
# START HANDLER
# ==========================
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /start"""
    ensure_dirs()
    welcome_text = (
        "🔥 *Deklan Fusion Bot*\n\n"
        "Multi-VPS Manager untuk Gensyn RL-Swarm Nodes\n\n"
        "📋 *Commands:*\n"
        "/addvps IP USER PASS - Tambah VPS\n"
        "/removevps IP - Hapus VPS\n"
        "/listvps - List VPS Anda\n"
        "/menu - Tampilkan menu\n\n"
        "📤 *Upload Keys*\n"
        "• swarm.pem\n"
        "• userApiKey.json\n"
        "• userData.json\n\n"
        "Keys akan auto-sync ke semua VPS Anda.\n"
    )
    if update.message:
        await update.message.reply_text(
            welcome_text,
            parse_mode="Markdown",
            reply_markup=main_menu()
        )


# ==========================
# MESSAGE HANDLER
# ==========================
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler utama untuk semua pesan TEXT & Document."""

    # Kalau ini document → dianggap upload keys
    if update.message and update.message.document:
        await handle_file(update, context)
        return

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # Commands
    if text.startswith("/addvps"):
        await add_vps(update, context)

    elif text.startswith("/removevps"):
        await remove_vps(update, context)

    elif text.startswith("/listvps"):
        await list_vps(update, context)

    elif text.startswith("/menu"):
        await update.message.reply_text(
            "📋 *Main Menu*",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

    # Menu Buttons (reply keyboard)
    elif text == "🖥 VPS Connect":
        await list_vps(update, context)

    elif text == "🔑 Upload Keys":
        await update.message.reply_text(
            "📤 Upload 3 keys:\n"
            "• swarm.pem\n• userApiKey.json\n• userData.json",
            parse_mode="Markdown"
        )

    elif text == "🟢 Node Status":
        await handle_node_status_all(update, context)

    elif text == "📈 Check Reward":
        await handle_check_reward(update, context)

    elif text == "💾 Swap Menu":
        await handle_swap_menu(update, context)

    elif text.startswith("Create ") and "Swap" in text:
        size = text.replace("Create ", "").replace(" Swap", "").strip()
        await handle_create_swap(update, context, size)

    elif text == "❌ Remove Swap":
        await handle_remove_swap(update, context)

    elif text == "🧹 Clean VPS":
        await handle_clean_vps(update, context)

    elif text == "⚙ Update Node":
        await handle_update_node(update, context)

    elif text == "🚀 Start Node":
        await handle_start_node_all(update, context)

    elif text == "🔄 Restart Node":
        await handle_restart_node_all(update, context)

    elif text == "📡 Peer Checker":
        await handle_peer_checker(update, context)

    elif text == "📊 Node Info":
        await handle_node_info_all(update, context)

    elif text == "⬅️ Back to Menu":
        await update.message.reply_text(
            "📋 *Main Menu*",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

    else:
        await update.message.reply_text(
            "❓ Command tidak dikenali. Gunakan /menu.",
            reply_markup=main_menu()
        )


# ==========================
# CALLBACK HANDLER
# ==========================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk semua callback query (inline button)."""
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data or ""

    # Node controls
    if data.startswith("node_status_"):
        await node_status(update, context)

    elif data.startswith("node_start_"):
        await node_start(update, context)

    elif data.startswith("node_restart_"):
        await node_restart(update, context)

    elif data.startswith("node_stop_"):
        await node_stop(update, context)

    elif data.startswith("node_logs_"):
        await node_logs(update, context)

    # VPS list/menu
    elif data == "vps_list" or data == "back_to_menu":
        await list_vps(update, context)

    elif data.startswith("vps_select_"):
        ip = data.replace("vps_select_", "")
        await show_vps_control(update, context, ip)

    else:
        await query.message.reply_text("❓ Action tidak dikenali.")


# ==========================
# STATUS ALL VPS
# ==========================
async def handle_node_status_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cek status rl-swarm.service di semua VPS milik user."""
    user_id = update.effective_user.id
    db = load_db()
    vps_list = get_user_vps_list(db, user_id)

    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS tersimpan.")
        return

    await update.message.reply_text("🔍 Mengecek status semua VPS...")

    results = []
    for ip, vps_data in vps_list.items():
        username = vps_data.get("user", "root")
        password = vps_data.get("password", "")

        success, output = SSHClient.execute(
            ip, username, password,
            "systemctl is-active rl-swarm.service 2>/dev/null || echo 'inactive'"
        )

        status = "🟢 active" if (success and "active" in (output or "")) else "🔴 inactive"
        results.append(f"`{ip}` → {status}")

    msg = "📊 *Status Semua VPS:*\n\n" + "\n".join(results)
    await update.message.reply_text(msg, parse_mode="Markdown")


# ==========================
# CHECK REWARD (ALL VPS)
# ==========================
async def handle_check_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cek reward semua node milik user."""
    user_id = update.effective_user.id
    db = load_db()
    vps_list = get_user_vps_list(db, user_id)

    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS tersimpan.")
        return

    await update.message.reply_text("📈 Mengecek reward...")

    results = []
    for ip, data in vps_list.items():
        username = data.get("user", "root")
        password = data.get("password", "")
        res = check_reward(ip, username, password)
        # Pastikan minimal ada ip di result
        if isinstance(res, dict):
            res.setdefault("ip", ip)
        results.append(res)

    msg_lines = ["🔥 *REWARD REPORT*\n"]
    for r in results:
        if not isinstance(r, dict):
            msg_lines.append("❌ Gagal baca data reward.\n")
            continue

        ip = r.get("ip", "N/A")
        status = r.get("status", "N/A")
        score = r.get("score", "N/A")
        reward = r.get("reward", "N/A")
        peer = r.get("peer", "N/A")

        msg_lines.append(
            f"IP: `{ip}`\n"
            f"Status: {status}\n"
            f"Score: {score}\n"
            f"Reward: {reward}\n"
            f"Peer: `{peer}`\n"
        )

    await update.message.reply_text("\n\n".join(msg_lines), parse_mode="Markdown")


# ==========================
# SWAP MENU
# ==========================
async def handle_swap_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan menu swap."""
    from .keyboard import swap_menu
    await update.message.reply_text(
        "💾 *Swap Menu*",
        parse_mode="Markdown",
        reply_markup=swap_menu()
    )


# ==========================
# CREATE SWAP
# ==========================
async def handle_create_swap(update: Update, context: ContextTypes.DEFAULT_TYPE, size: str):
    """Create swap di semua VPS user."""
    user_id = update.effective_user.id
    db = load_db()
    vps_list = get_user_vps_list(db, user_id)

    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS tersimpan.")
        return

    await update.message.reply_text(f"💾 Membuat swap {size} di semua VPS...")

    script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "create_swap.sh")

    success_count = 0
    fail_count = 0

    for ip, data in vps_list.items():
        username = data.get("user", "root")
        password = data.get("password", "")

        # Upload script
        up, msg = SSHClient.upload_file(
            ip, username, password,
            script_path, "/tmp/create_swap.sh"
        )
        if not up:
            fail_count += 1
            continue

        ok, out = SSHClient.execute(
            ip, username, password,
            f"chmod +x /tmp/create_swap.sh && bash /tmp/create_swap.sh {size}"
        )

        if ok:
            success_count += 1
        else:
            fail_count += 1

    await update.message.reply_text(
        f"📊 Summary:\n"
        f"✅ {success_count} VPS\n"
        f"❌ {fail_count} VPS",
        parse_mode="Markdown"
    )


# ==========================
# REMOVE SWAP
# ==========================
async def handle_remove_swap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove swap di semua VPS user."""
    user_id = update.effective_user.id
    db = load_db()
    vps_list = get_user_vps_list(db, user_id)

    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS.")
        return

    await update.message.reply_text("🗑 Menghapus swap...")

    success = 0
    fail = 0

    for ip, data in vps_list.items():
        ok, out = SSHClient.execute(
            ip, data.get("user", "root"), data.get("password", ""),
            "swapoff -a && rm -f /swapfile && sed -i '/swapfile/d' /etc/fstab"
        )
        if ok:
            success += 1
        else:
            fail += 1

    await update.message.reply_text(
        f"📊 Summary:\n"
        f"✅ {success} berhasil\n"
        f"❌ {fail} gagal",
        parse_mode="Markdown"
    )


# ==========================
# CLEAN VPS
# ==========================
async def handle_clean_vps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clean ringan semua VPS user (apt & journal)."""
    user_id = update.effective_user.id
    db = load_db()
    vps_list = get_user_vps_list(db, user_id)

    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS.")
        return

    await update.message.reply_text("🧹 Membersihkan semua VPS...")

    s = 0
    f = 0

    for ip, data in vps_list.items():
        ok, out = SSHClient.execute(
            ip, data.get("user", "root"), data.get("password", ""),
            "apt-get clean && apt-get autoremove -y && journalctl --vacuum-time=1d"
        )
        if ok:
            s += 1
        else:
            f += 1

    await update.message.reply_text(
        f"📊 Summary:\n"
        f"✅ {s}\n"
        f"❌ {f}",
        parse_mode="Markdown"
    )


# ==========================
# UPDATE NODE
# ==========================
async def handle_update_node(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jalankan scripts/update_node.sh di semua VPS user."""
    user_id = update.effective_user.id
    db = load_db()
    vps_list = get_user_vps_list(db, user_id)

    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS.")
        return

    await update.message.reply_text("⚙ Updating node di semua VPS...")

    script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "update_node.sh")

    success_count = 0
    fail_count = 0

    for ip, vps_data in vps_list.items():
        username = vps_data.get("user", "root")
        password = vps_data.get("password", "")

        upload_ok, msg = SSHClient.upload_file(
            ip, username, password,
            script_path, "/tmp/update_node.sh"
        )

        if not upload_ok:
            fail_count += 1
            await update.message.reply_text(
                f"❌ Upload gagal ke `{ip}`: {msg}",
                parse_mode="Markdown"
            )
            continue

        exec_ok, exec_out = SSHClient.execute(
            ip, username, password,
            "chmod +x /tmp/update_node.sh && bash /tmp/update_node.sh"
        )

        if exec_ok:
            success_count += 1
            await update.message.reply_text(
                f"✅ Node di `{ip}` updated",
                parse_mode="Markdown"
            )
        else:
            fail_count += 1
            await update.message.reply_text(
                f"❌ Update gagal di `{ip}`: {exec_out}",
                parse_mode="Markdown"
            )

    await update.message.reply_text(
        f"📊 Summary:\n"
        f"✅ {success_count}\n"
        f"❌ {fail_count}",
        parse_mode="Markdown"
    )


# ==========================
# SHOW VPS CONTROL
# ==========================
async def show_vps_control(update: Update, context: ContextTypes.DEFAULT_TYPE, ip: str):
    """Tampilkan control panel untuk 1 VPS (inline keyboard)."""
    user_id = update.effective_user.id
    db = load_db()

    if not is_vps_owner(db, ip, user_id):
        await update.callback_query.message.reply_text("❌ VPS bukan milik Anda.")
        return

    keyboard = vps_control_kb(ip)
    await update.callback_query.message.reply_text(
        f"🖥 *VPS Control: {ip}*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


# ==========================
# START NODE ALL
# ==========================
async def handle_start_node_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start rl-swarm.service di semua VPS user."""
    user_id = update.effective_user.id
    db = load_db()
    vps_list = get_user_vps_list(db, user_id)

    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS.")
        return

    await update.message.reply_text("🚀 Menjalankan node di semua VPS...")

    s = 0
    f = 0

    for ip, vps in vps_list.items():
        ok, out = SSHClient.execute(
            ip, vps.get("user", "root"), vps.get("password", ""),
            "systemctl start rl-swarm.service"
        )
        if ok:
            s += 1
        else:
            f += 1

    await update.message.reply_text(
        f"📊 Summary:\n"
        f"✅ {s}\n"
        f"❌ {f}",
        parse_mode="Markdown"
    )


# ==========================
# RESTART NODE ALL
# ==========================
async def handle_restart_node_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restart rl-swarm.service di semua VPS user."""
    user_id = update.effective_user.id
    db = load_db()
    vps_list = get_user_vps_list(db, user_id)

    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS.")
        return

    await update.message.reply_text("🔄 Merestart node di semua VPS...")

    s = 0
    f = 0

    for ip, vps_data in vps_list.items():
        ok, out = SSHClient.execute(
            ip, vps_data.get("user", "root"), vps_data.get("password", ""),
            "systemctl restart rl-swarm.service"
        )
        if ok:
            s += 1
        else:
            f += 1

    await update.message.reply_text(
        f"📊 Summary:\n"
        f"✅ {s}\n"
        f"❌ {f}",
        parse_mode="Markdown"
    )


# ==========================
# PEER CHECKER
# ==========================
async def handle_peer_checker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ambil Peer ID dari log di semua VPS user."""
    user_id = update.effective_user.id
    db = load_db()
    vps_list = get_user_vps_list(db, user_id)

    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS.")
        return

    await update.message.reply_text("📡 Mengecek Peer ID...")

    results = []
    for ip, vps in vps_list.items():
        ok, out = SSHClient.execute(
            ip, vps.get("user", "root"), vps.get("password", ""),
            "grep -o 'Qm[a-zA-Z0-9]\\{44,\\}' /root/rl-swarm/logs/swarm_launcher.log 2>/dev/null | tail -1 || echo 'N/A'"
        )
        peer = (out or "").strip() if ok else "N/A"
        results.append(f"`{ip}`: `{peer}`")

    msg = "📡 *Peer ID Semua VPS:*\n\n" + "\n".join(results)
    await update.message.reply_text(msg, parse_mode="Markdown")


# ==========================
# NODE INFO ALL
# ==========================
async def handle_node_info_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ambil info ringkas (status, score, reward, peer) semua node user."""
    user_id = update.effective_user.id
    db = load_db()
    vps_list = get_user_vps_list(db, user_id)

    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS.")
        return

    await update.message.reply_text("📊 Mengambil info semua node...")

    results = []
    for ip, vps in vps_list.items():
        r = check_reward(ip, vps.get("user", "root"), vps.get("password", ""))
        if isinstance(r, dict):
            r.setdefault("ip", ip)
        results.append(r)

    msg_lines = ["📊 *Node Info:*\n"]
    for r in results:
        if not isinstance(r, dict):
            msg_lines.append("❌ Gagal baca info node.\n")
            continue

        ip = r.get("ip", "N/A")
        status = r.get("status", "N/A")
        score = r.get("score", "N/A")
        reward = r.get("reward", "N/A")
        peer = r.get("peer", "N/A")

        msg_lines.append(
            f"IP: `{ip}`\n"
            f"Status: {status}\n"
            f"Score: {score}\n"
            f"Reward: {reward}\n"
            f"Peer: `{peer}`\n"
        )

    await update.message.reply_text("\n\n".join(msg_lines), parse_mode="Markdown")
