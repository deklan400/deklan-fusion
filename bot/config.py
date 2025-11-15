import os
from dotenv import load_dotenv

# ============================================================
# 🔁 LOAD GLOBAL ENV
# ============================================================
# .env berada di root project: /opt/deklan-fusion/.env
ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(ENV_PATH)


# ============================================================
# 🔧 BOT CONFIGURATION
# ============================================================

# Token bot Telegram (Wajib)
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not BOT_TOKEN:
    print("⚠️  WARNING: BOT_TOKEN kosong! Atur di .env → BOT_TOKEN=xxxxxx")


# ============================================================
# 👮 ADMIN CONFIG
# ============================================================

# ADMIN_IDS bisa banyak (comma-separated)
_raw_admins = os.getenv("ADMIN_IDS", os.getenv("ADMIN_ID", "")).strip()

ADMIN_IDS = []
if _raw_admins:
    for part in _raw_admins.split(","):
        part = part.strip()
        if part.isdigit():
            ADMIN_IDS.append(int(part))

# Chat untuk log broadcast
_admin_chat = os.getenv("ADMIN_CHAT_ID", "").strip()
ADMIN_CHAT_ID = int(_admin_chat) if _admin_chat.isdigit() else None


# ============================================================
# 📁 FOLDER STRUCTURE
# ============================================================

BASE_DIR = os.getenv("BASE_DIR", "/opt/deklan-fusion").rstrip("/")

KEY_DIR = os.path.join(BASE_DIR, "keys")
LOG_DIR = os.path.join(BASE_DIR, "logs")
TMP_DIR = os.path.join(BASE_DIR, "tmp")

DB_PATH = os.path.join(BASE_DIR, "fusion_db.json")


# ============================================================
# 🔑 GENSYN REQUIRED FILES
# ============================================================

KEY_SWARM = "swarm.pem"
KEY_API = "userApiKey.json"
KEY_USER = "userData.json"

NODE_KEYS_REQUIRED = [KEY_SWARM, KEY_API, KEY_USER]


# ============================================================
# 📦 FILE VALIDATION
# ============================================================
MAX_FILE_SIZE_MB = 5
ALLOWED_EXT = ["pem", "json"]


# ============================================================
# 🌐 DASHBOARD CONFIG (WEB PANEL)
# ============================================================

# URL publik dashboard (opsional)
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "").strip()

# Secret dashboard (WAJIB diganti untuk production)
DASHBOARD_SECRET_KEY = os.getenv("DASHBOARD_SECRET_KEY", "CHANGE_ME_SUPER_SECRET")

if DASHBOARD_SECRET_KEY == "CHANGE_ME_SUPER_SECRET":
    print("⚠️  WARNING: DASHBOARD_SECRET_KEY masih default!")

# JWT/session login expiration
try:
    DASHBOARD_TOKEN_EXPIRE = int(os.getenv("DASHBOARD_TOKEN_EXPIRE", "3600"))
except ValueError:
    DASHBOARD_TOKEN_EXPIRE = 3600


# ============================================================
# 📛 APP META
# ============================================================
APP_NAME = os.getenv("APP_NAME", "DeklanFusionBot")

