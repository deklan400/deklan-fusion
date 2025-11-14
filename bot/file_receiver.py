import os
import sys
import json
import logging
from telegram import Update
from telegram.ext import ContextTypes

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from config import KEY_DIR
from utils import ensure_dirs, validate_keys
from ssh_client import SSHClient

logger = logging.getLogger(__name__)

DB_PATH = "/opt/deklan-fusion/fusion_db.json"

# ===============================================
# Allowed filenames (harus EXACT)
# ===============================================
VALID_FILES = {
    "swarm.pem": "Private key untuk RL-Swarm",
    "userApiKey.json": "API Key Gensyn",
    "userData.json": "User Data Gensyn"
}

# Mapping filename ke remote path
REMOTE_PATHS = {
    "swarm.pem": "/root/ezlabs/swarm.pem",
    "userApiKey.json": "/root/ezlabs/userApiKey.json",
    "userData.json": "/root/ezlabs/userData.json"
}


def load_db():
    """Load database."""
    if not os.path.exists(DB_PATH):
        return {"vps": {}, "keys": {}}
    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except:
        return {"vps": {}, "keys": {}}


def save_db(data):
    """Save database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ===============================================
# File Receiver Handler
# ===============================================
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file upload dan auto-sync ke semua VPS."""
    chat_id = update.effective_chat.id
    bot = context.bot

    # handle jika user tidak kirim document
    if not update.message.document:
        await bot.send_message(
            chat_id,
            "⚠️ Kirim file berupa *document*, bukan foto!",
            parse_mode="Markdown"
        )
        return

    file = update.message.document
    filename = file.file_name

    # cek apakah file termasuk 3 file penting
    if filename not in VALID_FILES:
        await bot.send_message(
            chat_id,
            f"❌ *{filename}* tidak dikenal.\n\n"
            f"Hanya file berikut yang diperbolehkan:\n"
            f"• swarm.pem\n• userApiKey.json\n• userData.json",
            parse_mode="Markdown"
        )
        return

    # Ensure directories
    ensure_dirs()

    # ambil file (store per user untuk isolation)
    user_id = update.effective_user.id
    file_ref = await bot.get_file(file.file_id)
    # Store file dengan user_id prefix untuk isolation
    user_key_dir = os.path.join(KEY_DIR, str(user_id))
    os.makedirs(user_key_dir, exist_ok=True)
    file_path = os.path.join(user_key_dir, filename)
    await file_ref.download_to_drive(file_path)

    # Update database (per user)
    db = load_db()
    
    # Initialize user structure if not exists
    if "users" not in db:
        db["users"] = {}
    if str(user_id) not in db["users"]:
        db["users"][str(user_id)] = {"vps": {}, "keys": {}}
    
    db["users"][str(user_id)]["keys"][filename] = file_path
    save_db(db)

    # notif sukses
    await bot.send_message(
        chat_id,
        f"✅ File *{filename}* berhasil disimpan!\n"
        f"📁 Lokasi: `{file_path}`",
        parse_mode="Markdown"
    )

    # Auto-sync ke semua VPS
    await sync_keys_to_all_vps(update, context, filename, file_path)

    # cek apakah semua file sudah lengkap (check user's keys)
    user_keys = db["users"][str(user_id)]["keys"]
    missing = []
    required_files = ["swarm.pem", "userApiKey.json", "userData.json"]
    for req_file in required_files:
        if req_file not in user_keys:
            missing.append(req_file)
    
    if not missing:
        await bot.send_message(
            chat_id,
            "🎉 Semua *3 file penting* sudah lengkap!\n"
            "Bot siap menjalankan node ✔",
            parse_mode="Markdown"
        )
    else:
        await bot.send_message(
            chat_id,
            "📌 File tersimpan, tapi ada yang masih kurang:\n"
            + "\n".join([f"• {m}" for m in missing]),
            parse_mode="Markdown"
        )


async def sync_keys_to_all_vps(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                               filename: str, local_path: str):
    """Sync key file ke semua VPS user."""
    user_id = update.effective_user.id
    db = load_db()
    
    # Get user's VPS list
    if "users" not in db:
        db["users"] = {}
    if str(user_id) not in db["users"]:
        db["users"][str(user_id)] = {"vps": {}, "keys": {}}
    
    vps_list = db["users"][str(user_id)].get("vps", {})
    
    if not vps_list:
        await context.bot.send_message(
            update.effective_chat.id,
            "⚠ Tidak ada VPS yang tersimpan. Upload VPS dulu dengan /addvps"
        )
        return
    
    remote_path = REMOTE_PATHS.get(filename)
    if not remote_path:
        return
    
    await context.bot.send_message(
        update.effective_chat.id,
        f"🔄 Mengirim *{filename}* ke semua VPS Anda..."
    )
    
    success_count = 0
    for ip, vps_data in vps_list.items():
        username = vps_data.get("user", "root")
        password = vps_data.get("password", "")
        
        # Ensure remote directory exists
        remote_dir = os.path.dirname(remote_path)
        SSHClient.execute(ip, username, password, f"mkdir -p {remote_dir}")
        
        # Upload file
        success, msg = SSHClient.upload_file(ip, username, password, local_path, remote_path)
        
        if success:
            success_count += 1
            await context.bot.send_message(
                update.effective_chat.id,
                f"📤 {filename} → `{ip}` ✅",
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(
                update.effective_chat.id,
                f"❌ Gagal kirim ke `{ip}`: {msg}",
                parse_mode="Markdown"
            )
    
    await context.bot.send_message(
        update.effective_chat.id,
        f"✅ Sync selesai! {success_count}/{len(vps_list)} VPS berhasil."
    )
