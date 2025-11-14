import os
import json
import shutil
from datetime import datetime

# =========================================================
#  Path Helpers
# =========================================================

def ensure_dir(path: str):
    """Buat folder jika belum ada."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path


def ensure_dirs():
    """Ensure semua direktori penting sudah ada."""
    from config import KEY_DIR, LOG_DIR, TMP_DIR, BASE_DIR
    ensure_dir(BASE_DIR)
    ensure_dir(KEY_DIR)
    ensure_dir(LOG_DIR)
    ensure_dir(TMP_DIR)


def file_exists(path: str):
    """Cek apakah file ada."""
    return os.path.isfile(path)


def read_file(path: str):
    """Read raw file content."""
    try:
        with open(path, "r") as f:
            return f.read()
    except:
        return None


# =========================================================
#  JSON Helpers
# =========================================================

def load_json(path: str, default=None):
    """Load JSON aman, return default kalau error."""
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default


def save_json(path: str, data):
    """Safe save JSON."""
    ensure_dir(os.path.dirname(path))
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# =========================================================
#  File Upload Handler
# =========================================================

def save_uploaded_file(file_bytes, filename, dest_dir):
    """Simpan file yang dikirim user dari Telegram."""
    ensure_dir(dest_dir)
    dest_path = os.path.join(dest_dir, filename)

    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    return dest_path


def copy_file(src, dest):
    """Copy file aman."""
    ensure_dir(os.path.dirname(dest))
    shutil.copy2(src, dest)


# =========================================================
#  Key Validation
# =========================================================

REQUIRED_KEYS = [
    "swarm.pem",
    "userApiKey.json",
    "userData.json"
]

def validate_keys(key_dir):
    """Cek apakah 3 file penting sudah lengkap di key_dir."""
    missing = []
    for f in REQUIRED_KEYS:
        if not os.path.isfile(os.path.join(key_dir, f)):
            missing.append(f)
    return missing


# =========================================================
#  Logging helper
# =========================================================

def log(text, logfile):
    """Tulis log ke file + timestamp."""
    ensure_dir(os.path.dirname(logfile))
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(logfile, "a") as f:
        f.write(f"[{ts}] {text}\n")


# =========================================================
#  Formatting
# =========================================================

def pretty_json(data):
    """Format JSON jadi teks rapi."""
    return json.dumps(data, indent=2, ensure_ascii=False)
