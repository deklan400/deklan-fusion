from telegram import Update
from telegram.ext import ContextTypes
from config import KEY_DIR, VALID_KEYS
from utils import run_script
import os

async def handle_key_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    filename = doc.file_name

    if filename not in VALID_KEYS:
        await update.message.reply_text("❌ File tidak valid.\nUpload hanya:\n- swarm.pem\n- userApiKey.json\n- userData.json")
        return

    file_path = VALID_KEYS[filename]
    await doc.get_file().download_to_drive(file_path)

    await update.message.reply_text(f"✔ Key uploaded: {filename}\nSaved to: {file_path}")


async def create_swap(size):
    return run_script(f"create_swap.sh {size}")


async def remove_swap():
    return run_script("remove_swap.sh")


async def clean_vps():
    return run_script("clean_vps.sh")
