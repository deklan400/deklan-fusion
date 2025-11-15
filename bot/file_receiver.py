import os
import sys
import json
import logging
from telegram import Update
from telegram.ext import ContextTypes

# ===============================================================
#  FIX: PAKAI IMPORT BENAR (bot.config, bot.utils, bot.ssh_client)
# ===============================================================
from bot.config import KEY_DIR, NODE_KEYS_REQUIRED, DB_PATH, MAX_FILE_SIZE_MB
from bot.utils import ensure_dirs
from bot.ssh_client import SSHClient

logger = logging.getLogger(__name__)


# ===============================================================
#  FILE YANG DIIZINKAN (HARUS EXACT)
# ===============================================================
VALID_FILES = {
    "swarm.pem": "Private key RL-Swarm",
    "userApiKey.json": "API Key Gensyn",
    "userData.json": "User Data Gensyn"
}

REMOTE_PATHS = {
    "swarm.pem": "/root/ezlabs/swarm.pem",
    "userApiKey.json": "/root/ezlabs/userApiKey.json",
    "userData.json": "/root/ezlabs/userData.json"
}


# ===============================================================
#  DATABASE HANDLER
# ===============================================================
def load_db():
    if not os.path.exists(DB_PATH):
        return {"users": {}}
    try:
        with open(DB_PATH, "r") as f:
            db = json.load(f)
            if "users" not in db:
                db["users"] = {}
            return db
    except:
        return {"users": {}}


def save_db(data):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ===============================================================
#  MAIN HANDLER UNTUK FILE UPLOAD
# ===============================================================
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Tidak ada file → error
    if not update.message or not update.message.document:
        await update.message.reply_text(
            "⚠ Kirim file dalam bentuk *document*, bukan foto!",
            parse_mode="Markdown"
        )
        return

    document = update.message.document
    filename = document.file_name
    user_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id

    # ===========================================================
    # VALIDASI NAMA FILE
    # ===========================================================
    if filename not in VALID_FILES:
        await update.message.reply_text(
            f"❌ File *{filename}* tidak valid.\n\n"
            "Hanya file berikut yang diizinkan:\n"
            "• swarm.pem\n• userApiKey.json\n• userData.json",
            parse_mode="Markdown"
        )
        return

    # ===========================================================
    # VALIDASI FILE SIZE
    # ===========================================================
    file_size_mb = document.file_size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        await update.message.reply_text(
            f"❌ File terlalu besar.\nMaks: {MAX_FILE_SIZE_MB}MB",
            parse_mode="Markdown"
        )
        return

    # ===========================================================
    # FILE SAVE PER-USER
    # ===========================================================
    ensure_dirs()

    user_key_dir = os.path.join(KEY_DIR, user_id)
    os.makedirs(user_key_dir, exist_ok=True)

    file_path = os.path.join(user_key_dir, filename)

    tg_file = await context.bot.get_file(document.file_id)
    await tg_file.download_to_drive(file_path)

    # ===========================================================
    # UPDATE DATABASE
    # ===========================================================
    db = load_db()
    if user_id not in db["users"]:
        db["users"][user_id] = {"vps": {}, "keys": {}}

    db["users"][user_id]["keys"][filename] = file_path
    save_db(db)

    await update.message.reply_text(
        f"✅ *{filename}* berhasil disimpan!\n"
        f"📁 Lokasi: `{file_path}`",
        parse_mode="Markdown"
    )

    # ===========================================================
    # AUTO-SYNC KE SEMUA VPS USER
    # ===========================================================
    await sync_keys_to_all_vps(update, context, filename, file_path)

    # ===========================================================
    # CEK KELENGKAPAN SEMUA 3 FILE
    # ===========================================================
    user_keys = db["users"][user_id]["keys"]
    missing = [k for k in NODE_KEYS_REQUIRED if k not in user_keys]

    if not missing:
        await update.message.reply_text(
            "🎉 Semua *3 file Gensyn* sudah lengkap!\n"
            "Node siap dijalankan ✔",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "📝 File lengkap sebagian, masih kurang:\n" +
            "\n".join([f"• {m}" for m in missing]),
            parse_mode="Markdown"
        )


# ===============================================================
#  SYNC KE SEMUA VPS USER
# ===============================================================
async def sync_keys_to_all_vps(update, context, filename, local_path):
    user_id = str(update.effective_user.id)
    db = load_db()

    vps_list = db["users"].get(user_id, {}).get("vps", {})

    # Jika user belum punya VPS
    if not vps_list:
        await update.message.reply_text(
            "⚠ Tidak ada VPS tersimpan.\nTambah VPS dengan /addvps",
            parse_mode="Markdown"
        )
        return

    remote_path = REMOTE_PATHS.get(filename)
    if not remote_path:
        return

    await update.message.reply_text(
        f"🔄 Mengirim *{filename}* ke seluruh VPS…",
        parse_mode="Markdown"
    )

    success_count = 0

    for ip, vps in vps_list.items():
        username = vps["user"]
        password = vps["password"]

        # Pastikan folder remote ada
        SSHClient.execute(ip, username, password, f"mkdir -p {os.path.dirname(remote_path)}")

        ok, msg = SSHClient.upload_file(ip, username, password, local_path, remote_path)

        if ok:
            success_count += 1
            await update.message.reply_text(
                f"📤 {filename} → `{ip}` ✓",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"❌ Gagal kirim ke `{ip}`: {msg}",
                parse_mode="Markdown"
            )

    await update.message.reply_text(
        f"✅ Sync selesai! ({success_count}/{len(vps_list)} VPS berhasil)",
        parse_mode="Markdown"
    )
