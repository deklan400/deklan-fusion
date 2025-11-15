import os
import sys
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from bot.ssh_client import SSHClient   # FIXED PATH

DB_PATH = "/opt/deklan-fusion/fusion_db.json"
KEY_DIR = "/opt/deklan-fusion/keys"


# ======================================================
# DATABASE HANDLING
# ======================================================
def load_db():
    """Load DB dengan struktur terbaru (per-user VPS & per-user keys)."""
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


def ensure_user(db, user_id):
    """Pastikan user punya struktur lengkap."""
    uid = str(user_id)

    if uid not in db["users"]:
        db["users"][uid] = {"vps": {}, "keys": {}}

    return db["users"][uid]


def get_user_vps_list(db, user_id):
    return ensure_user(db, user_id)["vps"]


def get_user_keys(db, user_id):
    return ensure_user(db, user_id)["keys"]


def is_vps_owner(db, ip, user_id):
    return ip in get_user_vps_list(db, user_id)


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

    _, ip, username, passwd = args
    user_id = update.effective_user.id

    db = load_db()
    vps_list = get_user_vps_list(db, user_id)

    if ip in vps_list:
        await update.message.reply_text(
            f"⚠️ VPS `{ip}` sudah ada.", parse_mode="Markdown"
        )
        return

    vps_list[ip] = {"user": username, "password": passwd}
    save_db(db)

    await update.message.reply_text(
        f"🟢 VPS ditambahkan:\n• IP: `{ip}`\n• User: `{username}`",
        parse_mode="Markdown"
    )


# ======================================================
# LIST VPS
# ======================================================
async def list_vps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = load_db()
    vps_list = get_user_vps_list(db, user_id)

    if not vps_list:
        msg = (
            "❌ Tidak ada VPS tersimpan.\n\n"
            "Gunakan `/addvps IP USER PASS` untuk menambahkan."
        )
        if update.message:
            await update.message.reply_text(msg)
        else:
            await update.callback_query.message.reply_text(msg)
        return

    keyboard = [
        [InlineKeyboardButton(f"🖥 {ip}", callback_data=f"vps_select_{ip}")]
        for ip in vps_list
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")])

    text = f"📋 *Daftar VPS Anda ({len(vps_list)}):*\n\nPilih VPS untuk kontrol:"
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown",
                                        reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown",
                                                       reply_markup=InlineKeyboardMarkup(keyboard))


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
    vps_list = get_user_vps_list(db, user_id)

    if ip not in vps_list:
        await update.message.reply_text("❌ VPS tidak ditemukan.")
        return

    del vps_list[ip]
    save_db(db)

    await update.message.reply_text(
        f"🗑 VPS `{ip}` dihapus dari daftar Anda.",
        parse_mode="Markdown"
    )


# ======================================================
# FILE UPLOAD (3 KEYS)
# ======================================================
async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = load_db()
    keys = get_user_keys(db, user_id)

    document = update.message.document
    filename = document.file_name

    valid = ["swarm.pem", "userApiKey.json", "userData.json"]
    if filename not in valid:
        await update.message.reply_text(
            "❌ File tidak valid.\nUpload:\n- swarm.pem\n- userApiKey.json\n- userData.json"
        )
        return

    os.makedirs(KEY_DIR, exist_ok=True)

    bot_file = await context.bot.get_file(document.file_id)
    save_path = f"{KEY_DIR}/{user_id}_{filename}"
    await bot_file.download_to_drive(save_path)

    # SAVE KEYS PER USER
    keys[filename] = save_path
    save_db(db)

    await update.message.reply_text(f"🟢 `{filename}` tersimpan!", parse_mode="Markdown")


# ======================================================
# SYNC KEYS KE VPS
# ======================================================
async def sync_keys_to_all_vps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = load_db()

    keys = get_user_keys(db, user_id)
    vps_list = get_user_vps_list(db, user_id)

    if not keys:
        await update.message.reply_text("⚠ Belum ada keys diupload.")
        return

    if not vps_list:
        await update.message.reply_text("⚠ Tidak ada VPS tersimpan.")
        return

    await update.message.reply_text("🔄 Menyebarkan keys ke semua VPS…")

    for ip, vps in vps_list.items():
        u = vps["user"]
        p = vps["password"]

        # Directory yang benar untuk gensyn
        SSHClient.execute(ip, u, p, "mkdir -p /root/.config/gensyn")

        for fn, path in keys.items():
            remote = f"/root/.config/gensyn/{fn}"
            ok, msg = SSHClient.upload_file(ip, u, p, path, remote)

            if ok:
                await update.message.reply_text(f"📤 `{fn}` → `{ip}` OK", parse_mode="Markdown")
            else:
                await update.message.reply_text(f"❌ `{fn}` → `{ip}` gagal: {msg}", parse_mode="Markdown")

    await update.message.reply_text("✅ Sync selesai!")


# ======================================================
# VPS KEYBOARD
# ======================================================
def vps_control_kb(ip):
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
