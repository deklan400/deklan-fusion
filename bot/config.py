import os

BOT_TOKEN       = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID   = int(os.getenv("ADMIN_CHAT_ID", "0"))

BASE_DIR        = os.getenv("FUSION_DIR", "/opt/deklan-fusion")
KEY_DIR         = os.getenv("KEY_DIR", f"{BASE_DIR}/keys")
LOG_DIR         = f"{BASE_DIR}/logs"
SCRIPTS_DIR     = f"{BASE_DIR}/scripts"

# Valid key names for uploads
VALID_KEYS = {
    "swarm.pem": f"{KEY_DIR}/swarm.pem",
    "userApiKey.json": f"{KEY_DIR}/userApiKey.json",
    "userData.json": f"{KEY_DIR}/userData.json"
}
