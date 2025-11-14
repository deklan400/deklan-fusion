import os
from dotenv import load_dotenv

# Load .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ============================================================
# 🔧 BOT CONFIGURATION (Global)
# ============================================================

# NOTE:
# BOT_TOKEN tidak ditulis langsung di file
# tapi di-load dari environment variable (.env)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Admin ID (opsional)
ADMIN_ID = os.getenv("ADMIN_ID", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")

# ============================================================
# 🔧 FOLDER STRUCTURE
# ============================================================

BASE_DIR = "/opt/deklan-fusion"

KEY_DIR = os.path.join(BASE_DIR, "keys")
LOG_DIR = os.path.join(BASE_DIR, "logs")
TMP_DIR = os.path.join(BASE_DIR, "tmp")

# ============================================================
# 🔧 FILE NAMES FOR GENSYN NODE
# ============================================================

KEY_SWARM = "swarm.pem"
KEY_API = "userApiKey.json"
KEY_USER = "userData.json"

NODE_KEYS_REQUIRED = [KEY_SWARM, KEY_API, KEY_USER]

# ============================================================
# 🔧 LIMIT & VALIDATION
# ============================================================

MAX_FILE_SIZE_MB = 5  # maksimal upload 5MB
ALLOWED_EXT = ["pem", "json"]  # format file valid

