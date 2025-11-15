"""
Authentication & authorization utilities for Deklan Fusion Bot
"""

import os
from telegram import Update
from typing import List, Optional

# Load config
from bot.config import ADMIN_IDS


# ============================================================
# 🔍 GET LIST OF ADMIN USERS
# ============================================================
def get_admin_ids() -> List[int]:
    """
    Ambil daftar admin dari:
    - config.ADMIN_IDS (utama)
    - fallback ADMIN_ID (lama)
    - environment variable ADMIN_IDS / ADMIN_ID

    Returns list of admin user IDs as int.
    """

    # 1. Dari config (lebih prioritas)
    admin_list = list(ADMIN_IDS)

    # 2. Fallback environment
    env_admins = os.getenv("ADMIN_IDS", os.getenv("ADMIN_ID", "")).strip()

    if env_admins:
        for uid in env_admins.split(","):
            uid = uid.strip()
            if uid.isdigit():
                admin_list.append(int(uid))

    # Remove duplicate
    admin_list = list(set(admin_list))

    return admin_list


# ============================================================
# 🔐 CHECK ADMIN WITH TELEGRAM UPDATE
# ============================================================
def is_admin(update: Update) -> bool:
    """
    Check apakah user Telegram adalah admin.

    Args:
        update: Telegram Update object

    Returns:
        True jika admin, False kalau bukan
    """

    if not update or not update.effective_user:
        return False

    user_id = update.effective_user.id
    admin_ids = get_admin_ids()

    # Jika tidak ada admin ditentukan → default semua admin (untuk mode demo)
    if not admin_ids:
        return True

    return user_id in admin_ids


# ============================================================
# 🔐 CHECK ADMIN TANPA TELEGRAM (untuk Dashboard API)
# ============================================================
def is_admin_id(user_id: int) -> bool:
    """
    Cek apakah ID tertentu adalah admin.
    (Dipakai di dashboard login API)

    Args:
        user_id: integer Telegram user ID

    Returns:
        bool
    """
    if not isinstance(user_id, int):
        return False

    admin_ids = get_admin_ids()

    if not admin_ids:
        return True

    return user_id in admin_ids


# ============================================================
# 🛑 DECORATOR: AUTO-BLOCK NON-ADMIN
# ============================================================
def require_admin(func):
    """
    Dekorator untuk mengunci command tertentu
    agar hanya admin yang bisa akses.

    Usage:
        @require_admin
        async def function(update, context):
            ...
    """

    async def wrapper(update: Update, context, *args, **kwargs):
        if not is_admin(update):
            try:
                await update.message.reply_text(
                    "❌ *Akses Ditolak*\n\n"
                    "Command ini hanya untuk admin.",
                    parse_mode="Markdown"
                )
            except:
                pass
            return
        return await func(update, context, *args, **kwargs)

    return wrapper
