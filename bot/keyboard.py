from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Upload Keys", callback_data="upload_keys")],
        [InlineKeyboardButton("🧪 Node Controls", callback_data="node_menu")],
        [InlineKeyboardButton("💾 Swap Manager", callback_data="swap_menu")],
        [InlineKeyboardButton("🧹 Clean VPS", callback_data="clean_vps")],
        [InlineKeyboardButton("📊 Node Status", callback_data="node_status")],
    ])


def swap_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("32G", callback_data="swap_32")],
        [InlineKeyboardButton("50G", callback_data="swap_50")],
        [InlineKeyboardButton("80G", callback_data="swap_80")],
        [InlineKeyboardButton("100G", callback_data="swap_100")],
        [InlineKeyboardButton("❌ Remove Swap", callback_data="swap_remove")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_main")],
    ])


def node_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Start Node", callback_data="node_start")],
        [InlineKeyboardButton("⏹ Stop Node", callback_data="node_stop")],
        [InlineKeyboardButton("🔄 Restart Node", callback_data="node_restart")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_main")],
    ])
