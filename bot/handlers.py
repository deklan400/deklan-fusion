"""
Telegram Bot Handlers untuk Deklan Fusion.
"""
import os
import sys
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from config import KEY_DIR, TMP_DIR
from utils import ensure_dirs
from auth import is_admin, require_admin
from actions import (
    add_vps, remove_vps, list_vps,
    node_status, node_start, node_restart, node_stop, node_logs,
    sync_keys_to_all_vps, vps_control_kb
)
from file_receiver import handle_file
from keyboard import main_menu
from reward_checker import check_all_rewards, load_db
from ssh_client import SSHClient

logger = logging.getLogger(__name__)

DB_PATH = "/opt/deklan-fusion/fusion_db.json"


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /start command."""
    ensure_dirs()
    
    welcome_text = (
        "🔥 *Deklan Fusion Bot*\n\n"
        "Multi-VPS Manager untuk Gensyn RL-Swarm Nodes\n\n"
        "📋 *Commands:*\n"
        "/addvps IP USER PASS - Tambah VPS\n"
        "/removevps IP - Hapus VPS\n"
        "/listvps - List semua VPS Anda\n"
        "/menu - Tampilkan menu\n\n"
        "📤 *Upload Keys:*\n"
        "Kirim file: swarm.pem, userApiKey.json, userData.json\n\n"
        "Bot akan auto-sync keys ke semua VPS Anda.\n\n"
        "💡 *Tips:*\n"
        "• Anda bisa menambahkan banyak VPS\n"
        "• Setiap VPS terisolasi per user\n"
        "• Semua tombol bekerja untuk semua VPS Anda"
    )
    
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk text messages dan file uploads."""
    # Handle file uploads (public - setiap user upload keys mereka sendiri)
    if update.message.document:
        await handle_file(update, context)
        return
    
    # Handle text messages
    text = update.message.text.strip()
    
    # Commands (Public - setiap user manage VPS mereka sendiri)
    if text.startswith("/addvps"):
        await add_vps(update, context)
    elif text.startswith("/removevps"):
        await remove_vps(update, context)
    elif text.startswith("/listvps"):
        await list_vps(update, context)  # Public command
    elif text.startswith("/menu"):
        await update.message.reply_text(
            "📋 *Main Menu*",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    # Menu buttons
    elif text == "🖥 VPS Connect":
        await list_vps(update, context)
    elif text == "🔑 Upload Keys":
        await update.message.reply_text(
            "📤 *Upload Keys*\n\n"
            "Kirim file berikut:\n"
            "• swarm.pem\n"
            "• userApiKey.json\n"
            "• userData.json\n\n"
            "Bot akan auto-sync ke semua VPS.",
            parse_mode="Markdown"
        )
    elif text == "🟢 Node Status":
        await handle_node_status_all(update, context)
    elif text == "📈 Check Reward":
        await handle_check_reward(update, context)
    elif text == "💾 Swap Menu":
        await handle_swap_menu(update, context)
    elif text.startswith("Create ") and "Swap" in text:
        # Extract size dari text (e.g., "Create 32G Swap" -> "32G")
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
    elif text == "🛠 Update Bot":
        await update.message.reply_text(
            "🛠 *Update Bot*\n\n"
            "Bot version: 1.0.0\n"
            "Untuk update bot, jalankan di VPS:\n"
            "```bash\n"
            "cd /opt/deklan-fusion\n"
            "git pull\n"
            "systemctl restart fusion-bot\n"
            "```",
            parse_mode="Markdown"
        )
    elif text == "⬅️ Back to Menu":
        await update.message.reply_text(
            "📋 *Main Menu*",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    else:
        await update.message.reply_text(
            "❓ Command tidak dikenali. Gunakan /menu untuk melihat menu.",
            reply_markup=main_menu()
        )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk inline keyboard callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("node_status_"):
        ip = data.replace("node_status_", "")
        # Update callback data untuk node_status function
        update.callback_query.data = f"node_status_{ip}"
        await node_status(update, context)  # Public - read only
    elif data.startswith("node_start_"):
        ip = data.replace("node_start_", "")
        # Update callback data untuk node_start function
        update.callback_query.data = f"node_start_{ip}"
        await node_start(update, context)
    elif data.startswith("node_restart_"):
        ip = data.replace("node_restart_", "")
        # Update callback data untuk node_restart function
        update.callback_query.data = f"node_restart_{ip}"
        await node_restart(update, context)
    elif data.startswith("node_stop_"):
        ip = data.replace("node_stop_", "")
        # Update callback data untuk node_stop function
        update.callback_query.data = f"node_stop_{ip}"
        await node_stop(update, context)
    elif data.startswith("node_logs_"):
        ip = data.replace("node_logs_", "")
        # Update callback data untuk node_logs function
        update.callback_query.data = f"node_logs_{ip}"
        await node_logs(update, context)
    elif data == "vps_list" or data == "back_to_menu":
        await list_vps(update, context)
    elif data.startswith("vps_select_"):
        ip = data.replace("vps_select_", "")
        await show_vps_control(update, context, ip)
    else:
        await query.message.reply_text("❓ Action tidak dikenali.")


async def handle_node_status_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle status check untuk semua VPS user."""
    user_id = update.effective_user.id
    db = load_db()
    from actions import get_user_vps_list
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
        
        status = "🟢" if (success and "active" in output.lower()) else "🔴"
        results.append(f"{status} `{ip}`")
    
    msg = "📊 *Status Semua VPS:*\n\n" + "\n".join(results)
    await update.message.reply_text(msg, parse_mode="Markdown")


async def handle_check_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle check reward untuk semua VPS user."""
    user_id = update.effective_user.id
    await update.message.reply_text("📈 Mengecek rewards...")
    
    # Get user's VPS only
    db = load_db()
    from actions import get_user_vps_list
    user_vps_list = get_user_vps_list(db, user_id)
    
    if not user_vps_list:
        await update.message.reply_text("❌ Tidak ada VPS tersimpan.")
        return
    
    # Check rewards only for user's VPS
    results = []
    for ip, vps_data in user_vps_list.items():
        username = vps_data.get("user", "root")
        password = vps_data.get("password", "")
        from reward_checker import check_reward
        result = check_reward(ip, username, password)
        results.append(result)
    
    if not results:
        await update.message.reply_text("❌ Tidak ada VPS tersimpan.")
        return
    
    msg = "🔥 *CHANGE REPORT*\n\n"
    for r in results:
        status_emoji = "🟢" if r["status"] == "online" else "🔴"
        msg += (
            f"Label : {r['label']}\n"
            f"Peer  : {r['peer']}\n"
            f"{status_emoji}\n"
            f"Score : {r['score']}\n"
            f"Reward : {r['reward']}\n"
            f"Point  : {r['points']}\n\n"
        )
    
    msg += "Bot created by Deklan"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


async def handle_swap_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle swap menu."""
    from keyboard import swap_menu
    await update.message.reply_text(
        "💾 *Swap Menu*\n\nPilih ukuran swap:",
        parse_mode="Markdown",
        reply_markup=swap_menu()
    )


async def handle_create_swap(update: Update, context: ContextTypes.DEFAULT_TYPE, size: str):
    """Handle create swap untuk semua VPS user."""
    user_id = update.effective_user.id
    db = load_db()
    from actions import get_user_vps_list
    vps_list = get_user_vps_list(db, user_id)
    
    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS tersimpan.")
        return
    
    total_vps = len(vps_list)
    await update.message.reply_text(f"💾 Membuat swap {size} di {total_vps} VPS Anda...")
    
    # Script path
    script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "create_swap.sh")
    
    if not os.path.exists(script_path):
        await update.message.reply_text("❌ Script create_swap.sh tidak ditemukan.")
        return
    
    success_count = 0
    failed_count = 0
    
    for ip, vps_data in vps_list.items():
        username = vps_data.get("user", "root")
        password = vps_data.get("password", "")
        
        # Upload script ke VPS
        upload_success, upload_msg = SSHClient.upload_file(
            ip, username, password,
            script_path, "/tmp/create_swap.sh"
        )
        
        if not upload_success:
            await update.message.reply_text(f"❌ Gagal upload script ke `{ip}`: {upload_msg}", parse_mode="Markdown")
            continue
        
        # Execute script dengan parameter
        success, output = SSHClient.execute(
            ip, username, password,
            f"chmod +x /tmp/create_swap.sh && bash /tmp/create_swap.sh {size}"
        )
        
        if success:
            success_count += 1
            await update.message.reply_text(f"✅ Swap {size} dibuat di `{ip}`", parse_mode="Markdown")
        else:
            failed_count += 1
            await update.message.reply_text(f"❌ Gagal di `{ip}`: {output}", parse_mode="Markdown")
    
    # Summary
    await update.message.reply_text(
        f"📊 *Summary:*\n"
        f"✅ Berhasil: {success_count}/{total_vps}\n"
        f"❌ Gagal: {failed_count}/{total_vps}",
        parse_mode="Markdown"
    )


async def handle_remove_swap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle remove swap untuk semua VPS user."""
    user_id = update.effective_user.id
    db = load_db()
    from actions import get_user_vps_list
    vps_list = get_user_vps_list(db, user_id)
    
    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS tersimpan.")
        return
    
    total_vps = len(vps_list)
    await update.message.reply_text(f"🗑 Menghapus swap di {total_vps} VPS Anda...")
    
    success_count = 0
    failed_count = 0
    
    for ip, vps_data in vps_list.items():
        username = vps_data.get("user", "root")
        password = vps_data.get("password", "")
        
        success, output = SSHClient.execute(
            ip, username, password,
            "swapoff -a && rm -f /swapfile && sed -i '/swapfile/d' /etc/fstab"
        )
        
        if success:
            success_count += 1
            await update.message.reply_text(f"✅ Swap dihapus di `{ip}`", parse_mode="Markdown")
        else:
            failed_count += 1
            await update.message.reply_text(f"❌ Gagal di `{ip}`: {output}", parse_mode="Markdown")
    
    # Summary
    await update.message.reply_text(
        f"📊 *Summary:*\n"
        f"✅ Berhasil: {success_count}/{total_vps}\n"
        f"❌ Gagal: {failed_count}/{total_vps}",
        parse_mode="Markdown"
    )


async def handle_clean_vps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle clean VPS user."""
    user_id = update.effective_user.id
    db = load_db()
    from actions import get_user_vps_list
    vps_list = get_user_vps_list(db, user_id)
    
    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS tersimpan.")
        return
    
    total_vps = len(vps_list)
    await update.message.reply_text(f"🧹 Membersihkan {total_vps} VPS Anda...")
    
    success_count = 0
    failed_count = 0
    
    for ip, vps_data in vps_list.items():
        username = vps_data.get("user", "root")
        password = vps_data.get("password", "")
        
        success, output = SSHClient.execute(
            ip, username, password,
            "apt-get clean && apt-get autoremove -y && journalctl --vacuum-time=1d"
        )
        
        if success:
            success_count += 1
            await update.message.reply_text(f"✅ VPS `{ip}` dibersihkan", parse_mode="Markdown")
        else:
            failed_count += 1
            await update.message.reply_text(f"❌ Gagal di `{ip}`: {output}", parse_mode="Markdown")
    
    # Summary
    await update.message.reply_text(
        f"📊 *Summary:*\n"
        f"✅ Berhasil: {success_count}/{total_vps}\n"
        f"❌ Gagal: {failed_count}/{total_vps}",
        parse_mode="Markdown"
    )


async def handle_update_node(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle update node untuk semua VPS user."""
    user_id = update.effective_user.id
    db = load_db()
    from actions import get_user_vps_list
    vps_list = get_user_vps_list(db, user_id)
    
    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS tersimpan.")
        return
    
    total_vps = len(vps_list)
    await update.message.reply_text(f"⚙ Mengupdate node di {total_vps} VPS Anda...")
    
    script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "update_node.sh")
    
    if not os.path.exists(script_path):
        await update.message.reply_text("❌ Script update_node.sh tidak ditemukan.")
        return
    
    success_count = 0
    failed_count = 0
    
    for ip, vps_data in vps_list.items():
        username = vps_data.get("user", "root")
        password = vps_data.get("password", "")
        
        # Upload dan execute update script
            success, output = SSHClient.upload_file(
                ip, username, password,
                script_path, "/tmp/update_node.sh"
            )
            
            if success:
                exec_success, exec_output = SSHClient.execute(
                    ip, username, password,
                    "chmod +x /tmp/update_node.sh && bash /tmp/update_node.sh"
                )
                
                if exec_success:
                success_count += 1
                    await update.message.reply_text(f"✅ Node di `{ip}` diupdate", parse_mode="Markdown")
                else:
                failed_count += 1
                    await update.message.reply_text(f"❌ Gagal update di `{ip}`: {exec_output}", parse_mode="Markdown")
            else:
            failed_count += 1
                await update.message.reply_text(f"❌ Gagal upload script ke `{ip}`", parse_mode="Markdown")
    
    # Summary
    await update.message.reply_text(
        f"📊 *Summary:*\n"
        f"✅ Berhasil: {success_count}/{total_vps}\n"
        f"❌ Gagal: {failed_count}/{total_vps}",
        parse_mode="Markdown"
    )


async def show_vps_control(update: Update, context: ContextTypes.DEFAULT_TYPE, ip: str):
    """Show VPS control panel untuk IP tertentu."""
    user_id = update.effective_user.id
    db = load_db()
    from actions import get_user_vps_list, is_vps_owner
    
    # Check ownership
    if not is_vps_owner(db, ip, user_id):
        await update.callback_query.message.reply_text("❌ VPS tidak ditemukan atau bukan milik Anda.")
        return
    
    user_vps = get_user_vps_list(db, user_id)
    vps_data = user_vps.get(ip)
    
    if not vps_data:
        await update.callback_query.message.reply_text("❌ VPS tidak ditemukan.")
        return
    
    keyboard = vps_control_kb(ip)
    await update.callback_query.message.reply_text(
        f"🖥 *VPS Control: {ip}*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def handle_start_node_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle start node untuk semua VPS user."""
    user_id = update.effective_user.id
    db = load_db()
    from actions import get_user_vps_list
    vps_list = get_user_vps_list(db, user_id)
    
    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS tersimpan.")
        return
    
    total_vps = len(vps_list)
    await update.message.reply_text(f"🚀 Menjalankan node di {total_vps} VPS Anda...")
    
    success_count = 0
    failed_count = 0
    
    for ip, vps_data in vps_list.items():
        username = vps_data.get("user", "root")
        password = vps_data.get("password", "")
        
        success, output = SSHClient.execute(
            ip, username, password,
            "systemctl start rl-swarm.service"
        )
        
        if success:
            success_count += 1
            await update.message.reply_text(f"✅ Node di `{ip}` dijalankan", parse_mode="Markdown")
        else:
            failed_count += 1
            await update.message.reply_text(f"❌ Gagal di `{ip}`: {output}", parse_mode="Markdown")
    
    # Summary
    await update.message.reply_text(
        f"📊 *Summary:*\n"
        f"✅ Berhasil: {success_count}/{total_vps}\n"
        f"❌ Gagal: {failed_count}/{total_vps}",
        parse_mode="Markdown"
    )


async def handle_restart_node_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle restart node untuk semua VPS user."""
    user_id = update.effective_user.id
    db = load_db()
    from actions import get_user_vps_list
    vps_list = get_user_vps_list(db, user_id)
    
    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS tersimpan.")
        return
    
    total_vps = len(vps_list)
    await update.message.reply_text(f"🔄 Merestart node di {total_vps} VPS Anda...")
    
    success_count = 0
    failed_count = 0
    
    for ip, vps_data in vps_list.items():
        username = vps_data.get("user", "root")
        password = vps_data.get("password", "")
        
        success, output = SSHClient.execute(
            ip, username, password,
            "systemctl restart rl-swarm.service"
        )
        
        if success:
            success_count += 1
            await update.message.reply_text(f"✅ Node di `{ip}` direstart", parse_mode="Markdown")
        else:
            failed_count += 1
            await update.message.reply_text(f"❌ Gagal di `{ip}`: {output}", parse_mode="Markdown")
    
    # Summary
    await update.message.reply_text(
        f"📊 *Summary:*\n"
        f"✅ Berhasil: {success_count}/{total_vps}\n"
        f"❌ Gagal: {failed_count}/{total_vps}",
        parse_mode="Markdown"
    )


async def handle_peer_checker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle peer checker untuk semua VPS user."""
    user_id = update.effective_user.id
    db = load_db()
    from actions import get_user_vps_list
    vps_list = get_user_vps_list(db, user_id)
    
    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS tersimpan.")
        return
    
    await update.message.reply_text("📡 Mengecek peer ID semua VPS...")
    
    results = []
    for ip, vps_data in vps_list.items():
        username = vps_data.get("user", "root")
        password = vps_data.get("password", "")
        
        # Get peer ID from logs
        success, output = SSHClient.execute(
            ip, username, password,
            "grep -o 'Qm[a-zA-Z0-9]\{44,\}' /root/rl-swarm/logs/swarm_launcher.log 2>/dev/null | tail -1 || echo 'N/A'"
        )
        
        peer_id = output.strip() if success else "N/A"
        results.append(f"`{ip}`: `{peer_id}`")
    
    msg = "📡 *Peer ID Semua VPS:*\n\n" + "\n".join(results)
    await update.message.reply_text(msg, parse_mode="Markdown")


async def handle_node_info_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle node info untuk semua VPS user."""
    user_id = update.effective_user.id
    db = load_db()
    from actions import get_user_vps_list
    vps_list = get_user_vps_list(db, user_id)
    
    if not vps_list:
        await update.message.reply_text("❌ Tidak ada VPS tersimpan.")
        return
    
    await update.message.reply_text("📊 Mengambil info semua node...")
    
    # Check rewards only for user's VPS
    results = []
    for ip, vps_data in vps_list.items():
        username = vps_data.get("user", "root")
        password = vps_data.get("password", "")
        from reward_checker import check_reward
        result = check_reward(ip, username, password)
        results.append(result)
    
    if not results:
        await update.message.reply_text("❌ Tidak ada data node.")
        return
    
    msg = "📊 *Node Info:*\n\n"
    for r in results:
        status_emoji = "🟢" if r["status"] == "online" else "🔴"
        msg += (
            f"*Label {r['label']}*\n"
            f"Status: {status_emoji} {r['status']}\n"
            f"Peer: `{r['peer']}`\n"
            f"Score: {r['score']}\n"
            f"Reward: {r['reward']}\n"
            f"Points: {r['points']}\n\n"
        )
    
    await update.message.reply_text(msg, parse_mode="Markdown")

