"""
Monitor daemon untuk generate change report setiap 3 jam.
"""
import os
import sys
import json
import logging
import asyncio
import argparse
from datetime import datetime
from telegram import Bot
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load environment (if .env exists)
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
load_dotenv(env_path)

from bot.reward_checker import check_all_rewards, load_db
from bot.ssh_client import SSHClient

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def generate_change_report() -> str:
    """
    Generate change report untuk semua VPS.
    
    Returns:
        Formatted report string
    """
    results = check_all_rewards()
    
    if not results:
        return "❌ Tidak ada VPS tersimpan."
    
    # Format sesuai spesifikasi
    report = "🔥 CHANGE REPORT (3 HOURS)\n\n"
    
    for r in results:
        status_emoji = "🟢" if r["status"] == "online" else "🔴"
        report += (
            f"Label : {r['label']}\n"
            f"Peer  : {r['peer']}\n"
            f"{status_emoji}\n"
            f"Score : {r['score']}\n"
            f"Reward : {r['reward']}\n"
            f"Point  : {r['points']}\n\n"
        )
    
    report += "Bot created by Deklan"
    
    return report


async def send_report_to_admin(bot_token=None, admin_chat_id=None):
    """Send change report ke admin Telegram."""
    # Priority: function args > environment variable
    token = bot_token or os.getenv("BOT_TOKEN", "")
    chat_id = admin_chat_id or os.getenv("ADMIN_CHAT_ID", "")
    
    if not token or not chat_id:
        logger.error("BOT_TOKEN or ADMIN_CHAT_ID not set! Use --token and --admin-chat-id arguments or set environment variables")
        return
    
    try:
        bot = Bot(token=token)
        report = await generate_change_report()
        
        await bot.send_message(
            chat_id=chat_id,
            text=report,
            parse_mode="Markdown"
        )
        
        logger.info("Change report sent successfully")
        
    except Exception as e:
        logger.error(f"Error sending report: {e}")


async def check_node_errors():
    """Check untuk error di logs (ConnectionRefusedError, uvloop error, FileNotFoundError)."""
    db = load_db()
    
    # Support both old and new format
    vps_list = {}
    if "vps" in db:
        # Old format
    vps_list = db.get("vps", {})
    else:
        # New format - collect all VPS from all users
        for user_data in db.get("users", {}).values():
            vps_list.update(user_data.get("vps", {}))
    
    errors_found = []
    
    for ip, vps_data in vps_list.items():
        username = vps_data.get("user", "root")
        password = vps_data.get("password", "")
        
        # Get last 50 lines of log
        success, output = SSHClient.execute(
            ip, username, password,
            "tail -n 50 /root/rl-swarm/logs/swarm_launcher.log 2>/dev/null || echo ''"
        )
        
        if not success:
            continue
        
        # Check for common errors
        error_patterns = [
            "ConnectionRefusedError",
            "uvloop",
            "FileNotFoundError",
            "error",
            "Error",
            "ERROR",
            "exception",
            "Exception"
        ]
        
        for pattern in error_patterns:
            if pattern.lower() in output.lower():
                errors_found.append({
                    "ip": ip,
                    "error": pattern,
                    "log_snippet": output[-200:]  # Last 200 chars
                })
                break
    
    return errors_found


async def main(bot_token=None, admin_chat_id=None):
    """Main monitor loop."""
    logger.info("Starting Deklan Fusion Monitor...")
    
    while True:
        try:
            # Generate dan send report
            await send_report_to_admin(bot_token=bot_token, admin_chat_id=admin_chat_id)
            
            # Check for errors
            errors = await check_node_errors()
            if errors:
                logger.warning(f"Found {len(errors)} errors in VPS logs")
                # Optionally send error alerts to admin
            
            # Wait 3 hours (10800 seconds)
            await asyncio.sleep(10800)
            
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in monitor loop: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retry


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deklan Fusion Monitor")
    parser.add_argument(
        "--token",
        type=str,
        help="Telegram Bot Token (or set BOT_TOKEN environment variable)",
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
    if args.admin_chat_id:
        os.environ["ADMIN_CHAT_ID"] = args.admin_chat_id
    
    asyncio.run(main(bot_token=args.token, admin_chat_id=args.admin_chat_id))

