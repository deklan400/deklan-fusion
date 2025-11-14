"""
Authentication and authorization utilities.
"""
import os
from telegram import Update
from config import ADMIN_ID, ADMIN_CHAT_ID

# Support multiple admins (comma-separated)
def get_admin_ids():
    """Get list of admin IDs from environment."""
    admin_id_str = os.getenv("ADMIN_ID", ADMIN_ID)
    if not admin_id_str:
        return []
    
    # Support comma-separated admin IDs
    return [int(uid.strip()) for uid in admin_id_str.split(",") if uid.strip().isdigit()]


def is_admin(update: Update) -> bool:
    """
    Check if user is admin.
    
    Args:
        update: Telegram update object
        
    Returns:
        True if user is admin, False otherwise
    """
    if not update.effective_user:
        return False
    
    user_id = update.effective_user.id
    admin_ids = get_admin_ids()
    
    # If no admin configured, allow all (backward compatibility)
    if not admin_ids:
        return True
    
    return user_id in admin_ids


def require_admin(func):
    """
    Decorator to require admin access for a function.
    
    Usage:
        @require_admin
        async def admin_only_function(update, context):
            ...
    """
    async def wrapper(update: Update, context, *args, **kwargs):
        if not is_admin(update):
            await update.message.reply_text(
                "❌ *Akses Ditolak*\n\n"
                "Command ini hanya untuk admin.",
                parse_mode="Markdown"
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

