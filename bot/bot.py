import logging
import argparse
import os
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from bot.config import BOT_TOKEN
from bot.handlers import start_handler, message_handler, callback_handler
from bot.utils import ensure_dirs


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main(token=None):

    ensure_dirs()

    bot_token = token or os.getenv("BOT_TOKEN") or BOT_TOKEN
    if not bot_token:
        logger.error("BOT_TOKEN not set!")
        return

    app = ApplicationBuilder().token(bot_token).build()

    # Commands
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("addvps", message_handler))
    app.add_handler(CommandHandler("removevps", message_handler))
    app.add_handler(CommandHandler("listvps", message_handler))
    app.add_handler(CommandHandler("menu", message_handler))

    # Buttons
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Files and messages
    app.add_handler(MessageHandler(filters.Document.ALL, message_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("🔥 Deklan Fusion Bot started!")
    app.run_polling()   # <---- FIX PALING PENTING


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deklan Fusion Telegram Bot")
    parser.add_argument("--token", type=str, default=None)
    parser.add_argument("--admin-id", type=str, default=None)
    parser.add_argument("--admin-chat-id", type=str, default=None)
    args = parser.parse_args()

    if args.token:
        os.environ["BOT_TOKEN"] = args.token
    if args.admin_id:
        os.environ["ADMIN_ID"] = args.admin_id
    if args.admin_chat_id:
        os.environ["ADMIN_CHAT_ID"] = args.admin_chat_id

    main(token=args.token)   # <--- TIDAK ADA ASYNCIO.RUN !!
