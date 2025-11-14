import os
import time
import requests
from parser import parse_errors

FUSION_DIR = os.getenv("FUSION_DIR", "/opt/deklan-fusion")
LOG_PATH = f"{FUSION_DIR}/logs/node.log"
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

def send_alert(msg: str):
    """Send Telegram message"""
    if not BOT_TOKEN or not ADMIN_CHAT_ID:
        return
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_CHAT_ID,
        "text": msg
    }
    try:
        requests.post(url, json=payload)
    except Exception:
        pass


def get_latest_log():
    """Read last 500 lines of log"""
    if not os.path.isfile(LOG_PATH):
        return ""

    try:
        with open(LOG_PATH, "r") as f:
            lines = f.readlines()
            return "".join(lines[-500:])
    except:
        return ""


def main():
    if not os.path.exists(f"{FUSION_DIR}/logs"):
        os.makedirs(f"{FUSION_DIR}/logs")

    latest_log = get_latest_log()
    errors = parse_errors(latest_log)

    if errors:
        send_alert("🚨 *Deklan Fusion Detected Node Error!*\n"
                   f"Errors: `{', '.join(errors)}`")
    else:
        send_alert("🟢 Node status OK — no critical errors found.")

    return 0


if __name__ == "__main__":
    main()
