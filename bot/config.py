import os
from dotenv import load_dotenv

# ============================================================
# 🔁 LOAD .ENV (global)
# ============================================================
# .env ada di root project: /opt/deklan-fusion/.env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ============================================================
# 🔧 BOT CONFIGURATION (Global)
# ============================================================

# TOKEN bot Telegram (WAJIB)
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# ID admin utama (bisa lebih dari satu)
# Contoh di .env:
#   ADMIN_IDS=8099872387,123456789
_admin_ids_raw = os.getenv("ADMIN_IDS", os.getenv("ADMIN_ID", "")).strip()
ADMIN_IDS = []
if _admin_ids_raw:
    for part in _admin_ids_raw.split(","):
        part = part.strip()
        if part.isdigit():
            ADMIN_IDS.append(int(part))

# Chat ID admin untuk broadcast/log penting (opsional)
# Kalau kosong, bot akan kirim ke user pemicu saja.
_admin_chat = os.getenv("ADMIN_CHAT_ID", "").strip()
ADMIN_CHAT_ID = int(_admin_chat) if _admin_chat.isdigit() else None

# ============================================================
# 🔧 FOLDER STRUCTURE
# ============================================================

# Lokasi base di VPS (root project)
BASE_DIR = os.getenv("BASE_DIR", "/opt/deklan-fusion")

# Folder untuk keys, log, tmp
KEY_DIR = os.path.join(BASE_DIR, "keys")
LOG_DIR = os.path.join(BASE_DIR, "logs")
TMP_DIR = os.path.join(BASE_DIR, "tmp")

# Path database utama (dipakai bot & dashboard backend)
DB_PATH = os.path.join(BASE_DIR, "fusion_db.json")

# ============================================================
# 🔧 FILE NAMES UNTUK GENSYN NODE
# ============================================================

KEY_SWARM = "swarm.pem"
KEY_API = "userApiKey.json"
KEY_USER = "userData.json"

# List yang harus lengkap supaya node bisa jalan
NODE_KEYS_REQUIRED = [KEY_SWARM, KEY_API, KEY_USER]

# ============================================================
# 🔧 LIMIT & VALIDATION
# ============================================================

# Maksimal upload file (MB)
MAX_FILE_SIZE_MB = 5
# Ekstensi file yang diizinkan
ALLOWED_EXT = ["pem", "json"]

# ============================================================
# 🌐 DASHBOARD / API BACKEND CONFIG
# (disiapkan untuk web dashboard, tapi aman kalau belum dipakai)
# ============================================================

# URL publik dashboard (opsional, buat kirim link ke user dari bot)
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "").strip()

# Secret untuk sign token login (misal JWT) antara bot ↔ dashboard
# WAJIB diganti di production.
DASHBOARD_SECRET_KEY = os.getenv("DASHBOARD_SECRET_KEY", "CHANGE_ME_SUPER_SECRET")

# Waktu hidup token login dashboard (detik) – default 1 jam
try:
    DASHBOARD_TOKEN_EXPIRE = int(os.getenv("DASHBOARD_TOKEN_EXPIRE", "3600"))
except ValueError:
    DASHBOARD_TOKEN_EXPIRE = 3600

# Prefix / nama app untuk keperluan logging / multi-instance
APP_NAME = os.getenv("APP_NAME", "DeklanFusionBot")
