from telegram import KeyboardButton, ReplyKeyboardMarkup

# ======================================================
# MAIN MENU
# ======================================================
def main_menu():
    keyboard = [
        [KeyboardButton("🚀 Start Node"), KeyboardButton("🔄 Restart Node")],
        [KeyboardButton("🟢 Node Status"), KeyboardButton("📡 Peer Checker")],
        [KeyboardButton("📈 Check Reward"), KeyboardButton("📊 Node Info")],
        [KeyboardButton("🔑 Upload Keys"), KeyboardButton("🖥 VPS Connect")],
        [KeyboardButton("💾 Swap Menu"), KeyboardButton("🧹 Clean VPS")],
        [KeyboardButton("⚙ Update Node"), KeyboardButton("🛠 Update Bot")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ======================================================
# SWAP MENU
# ======================================================
def swap_menu():
    keyboard = [
        [KeyboardButton("Create 32G Swap"), KeyboardButton("Create 50G Swap")],
        [KeyboardButton("Create 80G Swap"), KeyboardButton("Create 100G Swap")],
        [KeyboardButton("❌ Remove Swap")],
        [KeyboardButton("⬅️ Back to Menu")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ======================================================
# VPS LOGIN MENU
# ======================================================
def vps_login_menu():
    keyboard = [
        [KeyboardButton("➕ Add VPS")],
        [KeyboardButton("📋 List VPS"), KeyboardButton("🗑 Remove VPS")],
        [KeyboardButton("⬅️ Back to Menu")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ======================================================
# CONFIRMATION MENU
# ======================================================
def confirm_menu():
    keyboard = [
        [KeyboardButton("✔ Yes"), KeyboardButton("✖ No")],
        [KeyboardButton("⬅️ Back")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

