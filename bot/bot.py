import logging
import argparse
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN
from handlers import start_handler, message_handler, callback_handler
from utils import ensure_dirs

# ---------------------------------------
# Logging
# ---------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------------------------------
# Main Bot Application
# ---------------------------------------
async def main(token=None):
    ensure_dirs()  # membuat folder keys/, logs/, tmp/

    # Priority: command line arg > environment variable > .env file
    bot_token = token or os.getenv("BOT_TOKEN") or BOT_TOKEN

    if not bot_token:
        logger.error("BOT_TOKEN not set! Use --token argument or set BOT_TOKEN environment variable")
        return

    app = ApplicationBuilder().token(bot_token).build()

    # Commands (all handled in message_handler)
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("addvps", message_handler))
    app.add_handler(CommandHandler("removevps", message_handler))
    app.add_handler(CommandHandler("listvps", message_handler))
    app.add_handler(CommandHandler("menu", message_handler))

    # Callback buttons
    app.add_handler(CallbackQueryHandler(callback_handler))

    # File uploads, messages, commands
    app.add_handler(MessageHandler(filters.Document.ALL, message_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("🔥 Deklan Fusion Bot started!")
    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    
    parser = argparse.ArgumentParser(description="Deklan Fusion Telegram Bot")
    parser.add_argument(
        "--token",
        type=str,
        help="Telegram Bot Token (or set BOT_TOKEN environment variable)",
        default=None
    )
    parser.add_argument(
        "--admin-id",
        type=str,
        help="Admin ID (or set ADMIN_ID environment variable)",
        default=None
    )
    parser.add_argument(
        "--admin-chat-id",
        type=str,
        help="Admin Chat ID (or set ADMIN_CHAT_ID environment variable)",
        default=None
    )
    
    args = parser.parse_args()
    
    # Set environment variables if provided via command line
    if args.token:
        os.environ["BOT_TOKEN"] = args.token
    if args.admin_id:
        os.environ["ADMIN_ID"] = args.admin_id
    if args.admin_chat_id:
        os.environ["ADMIN_CHAT_ID"] = args.admin_chat_id
    
    asyncio.run(main(token=args.token))
