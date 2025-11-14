import os
import sys
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from ssh_client import SSHClient

DB_PATH = "/opt/deklan-fusion/fusion_db.json"
KEY_DIR = "/opt/deklan-fusion/keys"


# ======================================================
# DATABASE HANDLING
# ======================================================
def load_db():
    if not os.path.exists(DB_PATH):
        return {"vps": {}, "keys": {}, "users": {}}
    try:
        with open(DB_PATH, "r") as f:
            db = json.load(f)
            # Migrate old format to new format
            if "users" not in db:
                db["users"] = {}
            return db
    except:
        return {"vps": {}, "keys": {}, "users": {}}


def save_db(data):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_user_vps_list(db, user_id: int):
    """Get VPS list untuk user tertentu."""
    if "users" not in db:
        db["users"] = {}
    if str(user_id) not in db["users"]:
        db["users"][str(user_id)] = {"vps": {}, "keys": {}}
    return db["users"][str(user_id)]["vps"]


def get_user_keys(db, user_id: int):
    """Get keys untuk user tertentu."""
    if "users" not in db:
        db["users"] = {}
    if str(user_id) not in db["users"]:
        db["users"][str(user_id)] = {"vps": {}, "keys": {}}
    return db["users"][str(user_id)]["keys"]


def is_vps_owner(db, ip: str, user_id: int) -> bool:
    """Check apakah user adalah owner dari VPS."""
    user_vps = get_user_vps_list(db, user_id)
    return ip in user_vps


# ======================================================
# ADD VPS
# ======================================================
async def add_vps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split()
    if len(args) != 4:
        await update.message.reply_text(
            "❌ Format salah.\nGunakan:\n`/addvps IP USER PASS`",
            parse_mode="Markdown"
        )
        return

    _, ip, user, passwd = args
    user_id = update.effective_user.id

    db = load_db()
    user_vps = get_user_vps_list(db, user_id)
    
    # Check if IP already exists for this user
    if ip in user_vps:
        await update.message.reply_text(f"⚠️ VPS `{ip}` sudah ada di daftar Anda.", parse_mode="Markdown")
        return
    
    user_vps[ip] = {"user": user, "password": passwd}
    save_db(db)

    await update.message.reply_text(f"🟢 VPS ditambahkan:\n• IP: `{ip}`\n• User: `{user}`", parse_mode="Markdown")


# ======================================================
# LIST VPS
# ======================================================
async def list_vps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = load_db()
    vps_list = get_user_vps_list(db, user_id)

    if not vps_list:
        if update.message:
            await update.message.reply_text(
                "❌ Tidak ada VPS tersimpan.\n\n"
                "Gunakan `/addvps IP USER PASS` untuk menambahkan VPS.",
                parse_mode="Markdown"
            )
        elif update.callback_query:
            await update.callback_query.message.reply_text(
                "❌ Tidak ada VPS tersimpan.\n\n"
                "Gunakan `/addvps IP USER PASS` untuk menambahkan VPS.",
                parse_mode="Markdown"
            )
        return

    # Create inline keyboard dengan tombol untuk setiap VPS
    keyboard = []
    for ip in vps_list:
        keyboard.append([InlineKeyboardButton(f"🖥 {ip}", callback_data=f"vps_select_{ip}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")])
    
    msg = f"📋 *Daftar VPS Anda ({len(vps_list)}):* \n\nPilih VPS untuk kontrol:"
    
    if update.message:
        await update.message.reply_text(
            msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ======================================================
# REMOVE VPS
# ======================================================
async def remove_vps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split()
    if len(args) != 2:
        await update.message.reply_text("Gunakan: `/removevps IP`", parse_mode="Markdown")
        return

    _, ip = args
    user_id = update.effective_user.id

    db = load_db()
    user_vps = get_user_vps_list(db, user_id)
    
    if ip in user_vps:
        del user_vps[ip]
        save_db(db)
        await update.message.reply_text(f"🗑 VPS `{ip}` dihapus dari daftar Anda.", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ VPS tidak ditemukan di daftar Anda.")


# ======================================================
# KEY UPLOAD HANDLER
# ======================================================
async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()

    document = update.message.document
    filename = document.file_name

    allowed = {
        "swarm.pem": "swarm",
        "userApiKey.json": "apikey",
        "userData.json": "userdata"
    }

    if filename not in allowed:
        await update.message.reply_text(
            "❌ File tidak dikenali.\nUpload salah satu dari:\n"
            "- swarm.pem\n- userApiKey.json\n- userData.json"
        )
        return

    os.makedirs(KEY_DIR, exist_ok=True)

    file = await context.bot.get_file(document.file_id)
    save_path = f"{KEY_DIR}/{filename}"
    await file.download_to_drive(save_path)

    db["keys"][allowed[filename]] = save_path
    save_db(db)

    await update.message.reply_text(f"🟢 `{filename}` tersimpan!", parse_mode="Markdown")

    await sync_keys_to_all_vps(update, context)


# ======================================================
# SYNC KEYS TO ALL VPS
# ======================================================
async def sync_keys_to_all_vps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = load_db()
    vps_list = get_user_vps_list(db, user_id)
    keys = get_user_keys(db, user_id)

    if not keys:
        await update.message.reply_text("⚠ Belum ada key yang diupload.")
        return

    if not vps_list:
        await update.message.reply_text("⚠ Tidak ada VPS yang tersimpan.")
        return

    await update.message.reply_text("🔄 Mengirim key ke semua VPS Anda…")

    for ip, data in vps_list.items():
        user = data["user"]
        passwd = data["password"]

        SSHClient.execute(ip, user, passwd, "mkdir -p /root/ezlabs")

        for keyname, filepath in keys.items():
            if os.path.exists(filepath):
                remote_path = f"/root/ezlabs/{os.path.basename(filepath)}"
                success, msg = SSHClient.upload_file(ip, user, passwd, filepath, remote_path)
                
                if success:
                    await update.message.reply_text(f"📤 {keyname} → `{ip}` ✅", parse_mode="Markdown")
                else:
                    await update.message.reply_text(f"❌ Gagal kirim ke `{ip}`: {msg}", parse_mode="Markdown")

    await update.message.reply_text("✅ Sync keys selesai!")


# ======================================================
# NODE STATUS
# ======================================================
async def node_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user_id = update.effective_user.id

    ip = update.callback_query.data.replace("node_status_", "")
    
    # Check ownership
    if not is_vps_owner(db, ip, user_id):
        await update.callback_query.message.reply_text("❌ VPS tidak ditemukan atau bukan milik Anda.")
        return
    
    user_vps = get_user_vps_list(db, user_id)
    vps = user_vps.get(ip)

    if not vps:
        await update.callback_query.message.reply_text("❌ VPS tidak ditemukan.")
        return

    user = vps["user"]
    passwd = vps["password"]

    msg = update.callback_query.message
    await msg.reply_text(f"🔍 Mengecek status node di `{ip}`…")

    success, status = SSHClient.execute(ip, user, passwd, "systemctl is-active rl-swarm.service")
    success, cpu = SSHClient.execute(ip, user, passwd, "grep 'cpu ' /proc/stat")
    success, ram = SSHClient.execute(ip, user, passwd, "free -h")
    success, disk = SSHClient.execute(ip, user, passwd, "df -h /")
    success, swap = SSHClient.execute(ip, user, passwd, "swapon --show --bytes")
    success, log = SSHClient.execute(ip, user, passwd, "tail -n 30 /root/rl-swarm/logs/swarm_launcher.log")

    text = (
        f"🖥 <b>Status Node — {ip}</b>\n"
        f"Service: <code>{status.strip()}</code>\n\n"
        f"💽 <b>CPU:</b>\n<code>{cpu[:200]}</code>\n\n"
        f"💾 <b>RAM:</b>\n<code>{ram}</code>\n\n"
        f"📀 <b>Disk:</b>\n<code>{disk}</code>\n\n"
        f"🔁 <b>Swap:</b>\n<code>{swap}</code>\n\n"
        f"📝 <b>Last Logs:</b>\n<code>{log}</code>"
    )

    await msg.reply_text(text, parse_mode="HTML")


# ======================================================
# NODE START
# ======================================================
async def node_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user_id = update.effective_user.id

    ip = update.callback_query.data.replace("node_start_", "")
    
    # Check ownership
    if not is_vps_owner(db, ip, user_id):
        await update.callback_query.answer("❌ VPS tidak ditemukan atau bukan milik Anda.", show_alert=True)
        return
    
    user_vps = get_user_vps_list(db, user_id)
    vps = user_vps.get(ip)

    if not vps:
        await update.callback_query.answer("❌ VPS tidak ditemukan.", show_alert=True)
        return

    user = vps["user"]
    passwd = vps["password"]

    msg = update.callback_query.message
    await msg.reply_text(f"▶️ Menjalankan node di `{ip}`…")

    SSHClient.execute(ip, user, passwd, "systemctl start rl-swarm.service")

    await msg.reply_text(f"🟢 Node di `{ip}` telah dijalankan.")


# ======================================================
# NODE RESTART
# ======================================================
async def node_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user_id = update.effective_user.id

    ip = update.callback_query.data.replace("node_restart_", "")
    
    # Check ownership
    if not is_vps_owner(db, ip, user_id):
        await update.callback_query.answer("❌ VPS tidak ditemukan atau bukan milik Anda.", show_alert=True)
        return
    
    user_vps = get_user_vps_list(db, user_id)
    vps = user_vps.get(ip)

    if not vps:
        await update.callback_query.answer("❌ VPS tidak ditemukan.", show_alert=True)
        return

    user = vps["user"]
    passwd = vps["password"]

    msg = update.callback_query.message
    await msg.reply_text(f"🔄 Restarting node di `{ip}`…")

    SSHClient.execute(ip, user, passwd, "systemctl restart rl-swarm.service")

    await msg.reply_text(f"🔄 Node restarted di `{ip}`")


# ======================================================
# NODE STOP
# ======================================================
async def node_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user_id = update.effective_user.id

    ip = update.callback_query.data.replace("node_stop_", "")
    
    # Check ownership
    if not is_vps_owner(db, ip, user_id):
        await update.callback_query.answer("❌ VPS tidak ditemukan atau bukan milik Anda.", show_alert=True)
        return
    
    user_vps = get_user_vps_list(db, user_id)
    vps = user_vps.get(ip)

    if not vps:
        await update.callback_query.answer("❌ VPS tidak ditemukan.", show_alert=True)
        return

    user = vps["user"]
    passwd = vps["password"]

    msg = update.callback_query.message
    await msg.reply_text(f"🛑 Stopping node di `{ip}`…")

    SSHClient.execute(ip, user, passwd, "systemctl stop rl-swarm.service")

    await msg.reply_text(f"🛑 Node stopped di `{ip}`")


# ======================================================
# VIEW NODE LOGS
# ======================================================
async def node_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user_id = update.effective_user.id

    ip = update.callback_query.data.replace("node_logs_", "")
    
    # Check ownership
    if not is_vps_owner(db, ip, user_id):
        await update.callback_query.message.reply_text("❌ VPS tidak ditemukan atau bukan milik Anda.")
        return
    
    user_vps = get_user_vps_list(db, user_id)
    vps = user_vps.get(ip)

    if not vps:
        await update.callback_query.message.reply_text("❌ VPS tidak ditemukan.")
        return

    user = vps["user"]
    passwd = vps["password"]

    msg = update.callback_query.message
    await msg.reply_text(f"📄 Mengambil log dari `{ip}`…")

    success, logs = SSHClient.execute(
        ip, user, passwd, "tail -n 60 /root/rl-swarm/logs/swarm_launcher.log"
    )

    await msg.reply_text(f"📄 <b>Logs:</b>\n<code>{logs}</code>", parse_mode="HTML")


# ======================================================
# KEYBOARD BUILDER
# ======================================================
def vps_control_kb(ip):
    """Create inline keyboard untuk VPS control."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Status", callback_data=f"node_status_{ip}")],
        [
            InlineKeyboardButton("▶️ Start", callback_data=f"node_start_{ip}"),
            InlineKeyboardButton("🔄 Restart", callback_data=f"node_restart_{ip}"),
            InlineKeyboardButton("🛑 Stop", callback_data=f"node_stop_{ip}")
        ],
        [InlineKeyboardButton("📄 Logs", callback_data=f"node_logs_{ip}")],
        [InlineKeyboardButton("⬅️ Back", callback_data="vps_list")]
    ])
