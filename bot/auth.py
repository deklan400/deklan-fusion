"""
Authentication & authorization utilities for Deklan Fusion Bot
"""

import os
from typing import List
from telegram import Update

# Load config
from bot.config import ADMIN_ID, ADMIN_CHAT_ID


# ============================================================
# 🔧 Normalizer: Convert string → list[int]
# ============================================================
def _parse_admin_list(value: str) -> List[int]:
    """Convert comma-separated string → list of admin IDs."""
    if not value:
        return []
    result = []
    for part in value.split(","):
        part = part.strip()
        if part.isdigit():
            result.append(int(part))
    return result


# ============================================================
# 🔍 GET LIST OF ADMIN USERS (FINAL)
# ============================================================
def get_admin_ids() -> List[int]:
    """
    Ambil daftar admin dari:
    - config.ADMIN_ID (lama)
    - config.ADMIN_CHAT_ID (opsional)
    - ENV ADMIN_ID, ADMIN_IDS
    - Bisa diperluas nanti dari DB

    Returns:
        list[int]
    """

    admin_ids = []

    # 1. From config.py
    if ADMIN_ID and str(ADMIN_ID).isdigit():
        admin_ids.append(int(ADMIN_ID))

    if ADMIN_CHAT_ID and str(ADMIN_CHAT_ID).isdigit():
        admin_ids.append(int(ADMIN_CHAT_ID))

    # 2. ENV: ADMIN_IDS
    env_multi = os.getenv("ADMIN_IDS", "")
    admin_ids += _parse_admin_list(env_multi)

    # 3. ENV: ADMIN_ID single
    env_single = os.getenv("ADMIN_ID", "")
    if env_single.isdigit():
        admin_ids.append(int(env_single))

    # Cleanup duplicate
    admin_ids = list(set(admin_ids))

    return admin_ids


# ============================================================
# 🔐 CHECK ADMIN VIA TELEGRAM UPDATE
# ============================================================
def is_admin(update: Update) -> bool:
    if not update or not update.effective_user:
        return False

    user_id = update.effective_user.id
    admin_list = get_admin_ids()

    # Jika tidak ada admin → ALLOW DEV MODE (opsional)
    if not admin_list:
        return True   # Mode development (boleh semua)

    return user_id in admin_list


# ============================================================
# 🔐 CHECK ADMIN BY ID (untuk Dashboard Login API)
# ============================================================
def is_admin_id(user_id: int) -> bool:
    if not isinstance(user_id, int):
        return False

    admin_list = get_admin_ids()

    if not admin_list:
        return True  # fallback dev mode

    return user_id in admin_list


# ============================================================
# 🛑 DECORATOR: BLOCK NON-ADMIN
# ============================================================
def require_admin(func):
    async def wrapper(update: Update, context, *args, **kwargs):
        if not is_admin(update):
            try:
                await update.message.reply_text(
                    "❌ *Akses Ditolak*\n\n"
                    "Hanya admin yang bisa memakai command ini.",
                    parse_mode="Markdown"
                )
            except:
                pass
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
