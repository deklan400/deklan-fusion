import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN, ADMIN_CHAT_ID
from keyboard import main_menu, swap_menu, node_menu
from actions import handle_key_upload, create_swap, remove_swap, clean_vps

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return await update.message.reply_text("❌ Access denied.")

    await update.message.reply_text("🔥 Deklan Fusion Online!", reply_markup=main_menu())

async def callback(update: Update, context):
    query = update.callback_query
    await query.answer()

    cid = query.data

    if cid == "upload_keys":
        await query.edit_message_text("📥 Kirim file swarm.pem, userApiKey.json, userData.json satu per satu.")
    
    elif cid == "swap_menu":
        await query.edit_message_text("💾 Swap Manager", reply_markup=swap_menu())

    elif cid == "clean_vps":
        out = await clean_vps()
        await query.edit_message_text(f"🧹 VPS cleaned:\n```\n{out}\n```", parse_mode="Markdown")

    elif cid.startswith("swap_"):
        size = cid.replace("swap_", "")
        out = await create_swap(size)
        await query.edit_message_text(f"✔ Swap {size}G created:\n```\n{out}\n```", parse_mode="Markdown")

    elif cid == "swap_remove":
        out = await remove_swap()
        await query.edit_message_text(f"❌ Swap removed:\n```\n{out}\n```", parse_mode="Markdown")

    elif cid == "back_main":
        await query.edit_message_text("🔥 Deklan Fusion Online!", reply_markup=main_menu())

async def recv_doc(update: Update, context):
    await handle_key_upload(update, context)

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.Document.ALL, recv_doc))

    app.run_polling()

if __name__ == "__main__":
    main()
