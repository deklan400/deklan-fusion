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


# ============================================================
# LOGGING CONFIG
# ============================================================
logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("DeklanFusionBot")


# ============================================================
# MAIN BOT STARTER
# ============================================================
def main(token=None):

    ensure_dirs()  # Create keys, logs, tmp if not exist

    # Token handling
    bot_token = token or os.getenv("BOT_TOKEN") or BOT_TOKEN
    if not bot_token:
        logger.error("❌ BOT_TOKEN tidak ditemukan! Set di .env atau argumen.")
        return

    logger.info("🔄 Initializing Telegram Bot…")

    # Build Application
    app = ApplicationBuilder().token(bot_token).build()

    # --------------------------------------------------------
    # COMMAND HANDLERS
    # --------------------------------------------------------
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("addvps", message_handler))
    app.add_handler(CommandHandler("removevps", message_handler))
    app.add_handler(CommandHandler("listvps", message_handler))
    app.add_handler(CommandHandler("menu", message_handler))

    # --------------------------------------------------------
    # CALLBACK QUERY (BUTTON HANDLER)
    # --------------------------------------------------------
    app.add_handler(CallbackQueryHandler(callback_handler))

    # --------------------------------------------------------
    # MESSAGE & FILE HANDLER
    # --------------------------------------------------------
    # File upload (keys)
    app.add_handler(MessageHandler(filters.Document.ALL, message_handler))

    # Normal text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # --------------------------------------------------------
    # BOT ONLINE
    # --------------------------------------------------------
    logger.info("🔥 Deklan Fusion Bot started and running!")
    app.run_polling(close_loop=False)  # prevent asyncio loop breaking


# ============================================================
# ENTRYPOINT (CLI arguments)
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deklan Fusion Telegram Bot")

    parser.add_argument("--token", type=str, default=None)
    parser.add_argument("--admin-id", type=str, default=None)
    parser.add_argument("--admin-chat-id", type=str, default=None)

    args = parser.parse_args()

    # Override environment if provided
    if args.token:
        os.environ["BOT_TOKEN"] = args.token

    if args.admin_id:
        os.environ["ADMIN_ID"] = args.admin_id

    if args.admin_chat_id:
        os.environ["ADMIN_CHAT_ID"] = args.admin_chat_id

    # Start
    main(token=args.token)
