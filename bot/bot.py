#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Deklan Fusion Bot
Unified Telegram controller for Gensyn RL-Swarm + VPS utilities.

Requirements (bot/requirements.txt):
    python-telegram-bot==21.6
    psutil==6.0.0
"""

import asyncio
import json
import os
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import psutil
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ======================================================================
# ENV + GLOBAL CONFIG
# ======================================================================

BASE_DIR = Path(__file__).resolve().parent.parent  # /opt/deklan-fusion
BOT_DIR = BASE_DIR / "bot"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

SWAP_LOG = LOG_DIR / "swap_history.json"
DEFAULT_ENV_PATH = BOT_DIR / ".env"


def load_env(path: Path = DEFAULT_ENV_PATH) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    # allow process env override
    env.update({k: v for k, v in os.environ.items()})
    return env


ENV = load_env()

BOT_TOKEN = ENV.get("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = ENV.get("CHAT_ID", "").strip()
ALLOWED_USER_IDS: List[str] = []

if ADMIN_CHAT_ID:
    ALLOWED_USER_IDS.append(ADMIN_CHAT_ID)

extra_ids = ENV.get("ALLOWED_USER_IDS", "")
if extra_ids:
    for x in extra_ids.split(","):
        x = x.strip()
        if x:
            ALLOWED_USER_IDS.append(x)

SERVICE_NAME = ENV.get("SERVICE_NAME", "rl-swarm")
NODE_NAME = ENV.get("NODE_NAME", "Deklan-Node")
RL_DIR = Path(ENV.get("RL_DIR", "/root/rl-swarm"))
KEY_DIR = Path(ENV.get("KEY_DIR", "/root/deklan"))
FUSION_DIR = Path(ENV.get("FUSION_DIR", str(BASE_DIR)))
AUTO_INSTALLER_GITHUB = ENV.get(
    "AUTO_INSTALLER_GITHUB",
    "https://raw.githubusercontent.com/deklan400/deklan-fusion/main/",
)

SWAPFILE = Path("/swapfile")

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN not set in .env or environment!")


# ======================================================================
# HELPERS
# ======================================================================


def is_allowed(update: Update) -> bool:
    """Check if user is allowed to use bot."""
    user_id = None
    if update.effective_user:
        user_id = str(update.effective_user.id)
    if not user_id:
        return False
    return (not ALLOWED_USER_IDS) or (user_id in ALLOWED_USER_IDS)


async def ensure_allowed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if is_allowed(update):
        return True
    if update.effective_message:
        await update.effective_message.reply_text("⛔️ Kamu tidak diizinkan memakai bot ini.")
    return False


def run_cmd(cmd: str, timeout: int = 300) -> subprocess.CompletedProcess:
    """
    Run shell command with bash -lc.
    Returns CompletedProcess (stdout/stderr decoded to utf-8).
    """
    proc = subprocess.run(
        ["bash", "-lc", cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        text=True,
    )
    return proc


def append_swap_log(entry: Dict[str, Any]) -> None:
    try:
        data: List[Dict[str, Any]] = []
        if SWAP_LOG.is_file():
            data = json.loads(SWAP_LOG.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                data = []
        data.append(entry)
        SWAP_LOG.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        # best-effort; jangan sampe bot mati cuma karena gagal log
        pass


def get_swap_status() -> str:
    try:
        with open("/proc/swaps", "r", encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
        if len(lines) <= 1:
            return "Tidak ada swap aktif."
        info_lines = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 5:
                filename, size_kb, used_kb = parts[0], int(parts[2]), int(parts[3])
                size_gb = size_kb / (1024 * 1024)
                used_gb = used_kb / (1024 * 1024)
                info_lines.append(
                    f"- {filename} → {size_gb:.1f}G (dipakai {used_gb:.2f}G)"
                )
        return "\n".join(info_lines)
    except Exception as e:
        return f"Gagal baca swap status: {e}"


def human_size(num_bytes: int) -> str:
    for unit in ["B", "K", "M", "G", "T"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f}{unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f}P"


# ======================================================================
# KEYBOARDS
# ======================================================================


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🟢 Status Node", callback_data="status"),
                InlineKeyboardButton("🔄 Restart Node", callback_data="restart_node"),
            ],
            [
                InlineKeyboardButton("💾 Swap Manager", callback_data="swap_menu"),
                InlineKeyboardButton("🧹 Clean VPS", callback_data="clean_vps"),
            ],
            [
                InlineKeyboardButton("📦 Install Node", callback_data="install_node"),
                InlineKeyboardButton("🗝 Upload Keys", callback_data="upload_keys_info"),
            ],
            [
                InlineKeyboardButton("📊 Monitor Now", callback_data="monitor_now"),
                InlineKeyboardButton("🔧 Tools", callback_data="tools_menu"),
            ],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu"),
                InlineKeyboardButton("🆕 Check Update", callback_data="update_check"),
            ],
        ]
    )


def swap_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("32G", callback_data="swap_32"),
                InlineKeyboardButton("50G", callback_data="swap_50"),
            ],
            [
                InlineKeyboardButton("80G", callback_data="swap_80"),
                InlineKeyboardButton("100G", callback_data="swap_100"),
            ],
            [
                InlineKeyboardButton("150G", callback_data="swap_150"),
                InlineKeyboardButton("200G", callback_data="swap_200"),
            ],
            [InlineKeyboardButton("❌ Remove Swap", callback_data="swap_remove")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_main")],
        ]
    )


def tools_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📄 View Logs", callback_data="tools_logs"),
                InlineKeyboardButton("🛑 Stop Node", callback_data="tools_stop"),
            ],
            [
                InlineKeyboardButton("💀 Kill Python", callback_data="tools_kill_py"),
                InlineKeyboardButton("🐳 Fix Docker", callback_data="tools_fix_docker"),
            ],
            [
                InlineKeyboardButton(
                    "🗑 Delete RL-Swarm", callback_data="tools_delete_swarm"
                ),
            ],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_main")],
        ]
    )


def settings_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔤 Set Node Name", callback_data="set_node_name"),
                InlineKeyboardButton(
                    "🔧 Set Service", callback_data="set_service_name"
                ),
            ],
            [
                InlineKeyboardButton(
                    "👤 Allowed Users", callback_data="set_allowed_users"
                ),
                InlineKeyboardButton("📁 Set Paths", callback_data="set_paths"),
            ],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_main")],
        ]
    )


# ======================================================================
# CORE BOT HANDLERS
# ======================================================================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update, context):
        return

    text = (
        f"🔥 <b>Deklan Fusion</b>\n"
        f"Node: <code>{NODE_NAME}</code>\n"
        f"Service: <code>{SERVICE_NAME}</code>\n\n"
        "Gunakan tombol di bawah untuk kontrol node & VPS."
    )
    await update.effective_message.reply_text(
        text, reply_markup=main_menu(), parse_mode=ParseMode.HTML
    )


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update, context):
        return

    query = update.callback_query
    if not query:
        return
    await query.answer()

    data = query.data or ""
    msg: Message = query.message

    # Navigation
    if data == "back_main":
        await msg.edit_text(
            "🏠 Main menu:", reply_markup=main_menu(), parse_mode=ParseMode.HTML
        )
        return

    # ---- Status & restart ----
    if data == "status":
        await show_status(msg)
    elif data == "restart_node":
        await restart_node(msg)
    # ---- Swap menu ----
    elif data == "swap_menu":
        await msg.edit_text(
            f"💾 <b>Swap Manager</b>\n\n"
            f"Swap aktif sekarang:\n<code>{get_swap_status()}</code>\n\n"
            "Pilih ukuran swap yang ingin dibuat:",
            reply_markup=swap_menu_kb(),
            parse_mode=ParseMode.HTML,
        )
    elif data.startswith("swap_"):
        size_map = {
            "swap_32": 32,
            "swap_50": 50,
            "swap_80": 80,
            "swap_100": 100,
            "swap_150": 150,
            "swap_200": 200,
        }
        if data == "swap_remove":
            await remove_swap(msg)
        else:
            size = size_map.get(data)
            if size:
                await create_swap(msg, size_gb=size)
    # ---- Clean VPS ----
    elif data == "clean_vps":
        await clean_vps(msg)
    # ---- Install Node ----
    elif data == "install_node":
        await install_node(msg)
    # ---- Keys ----
    elif data == "upload_keys_info":
        await msg.edit_text(
            "🗝 <b>Upload Keys</b>\n\n"
            "Kirim file berikut <b>satu per satu</b> ke chat ini:\n"
            "• <code>swarm.pem</code>\n"
            "• <code>userApiKey.json</code>\n"
            "• <code>userData.json</code>\n\n"
            f"Bot akan menyimpan ke: <code>{KEY_DIR}</code>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Back", callback_data="back_main")]]
            ),
            parse_mode=ParseMode.HTML,
        )
    # ---- Monitor ----
    elif data == "monitor_now":
        await monitor_now(msg)
    # ---- Tools ----
    elif data == "tools_menu":
        await msg.edit_text(
            "🔧 <b>Tools</b> (advanced):",
            reply_markup=tools_menu_kb(),
            parse_mode=ParseMode.HTML,
        )
    elif data == "tools_logs":
        await view_logs(msg)
    elif data == "tools_stop":
        await stop_node(msg)
    elif data == "tools_kill_py":
        await kill_python(msg)
    elif data == "tools_fix_docker":
        await fix_docker(msg)
    elif data == "tools_delete_swarm":
        await delete_rlswarm(msg)
    # ---- Settings ----
    elif data == "settings_menu":
        await msg.edit_text(
            "⚙️ <b>Settings</b>\n\n"
            "Beberapa pengaturan masih manual lewat file .env, "
            "tapi menu ini jadi pusat konfigurasi ke depan.",
            reply_markup=settings_menu_kb(),
            parse_mode=ParseMode.HTML,
        )
    elif data in {"set_node_name", "set_service_name", "set_allowed_users", "set_paths"}:
        await msg.reply_text(
            "⚙️ Setting ini sementara masih manual.\n"
            "Edit file <code>bot/.env</code> lalu restart bot:\n"
            "<code>systemctl restart deklan-fusion-bot</code>",
            parse_mode=ParseMode.HTML,
        )
    # ---- Update check ----
    elif data == "update_check":
        await check_update(msg)


# ======================================================================
# ACTION IMPLEMENTATIONS
# ======================================================================


async def show_status(msg: Message) -> None:
    # systemctl status
    node_status = run_cmd(f"systemctl is-active {shlex.quote(SERVICE_NAME)}")
    active = node_status.stdout.strip()

    # simple stats
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    swap_info = get_swap_status()

    text = (
        f"🟢 <b>Status Node</b> (<code>{NODE_NAME}</code>)\n"
        f"Service: <code>{SERVICE_NAME}</code> → "
        f"<b>{active or 'unknown'}</b>\n\n"
        f"💻 CPU: <code>{cpu:.1f}%</code>\n"
        f"💾 RAM: <code>{mem.percent:.1f}% "
        f"({human_size(mem.used)}/{human_size(mem.total)})</code>\n"
        f"💽 Disk: <code>{disk.percent:.1f}% "
        f"({human_size(disk.used)}/{human_size(disk.total)})</code>\n\n"
        f"🔁 Swap:\n<code>{swap_info}</code>"
    )

    await msg.reply_text(text, parse_mode=ParseMode.HTML)


async def restart_node(msg: Message) -> None:
    await msg.reply_text("🔄 Restarting node…")
    proc = run_cmd(f"systemctl restart {shlex.quote(SERVICE_NAME)} || true")
    if proc.returncode == 0:
        await msg.reply_text("✅ Node restart dikirim. Cek status beberapa detik lagi.")
    else:
        await msg.reply_text(
            f"⚠️ Gagal restart node.\n<code>{proc.stderr}</code>",
            parse_mode=ParseMode.HTML,
        )


async def stop_node(msg: Message) -> None:
    await msg.reply_text("🛑 Stopping node…")
    proc = run_cmd(f"systemctl stop {shlex.quote(SERVICE_NAME)} || true")
    if proc.returncode == 0:
        await msg.reply_text("✅ Node stop dikirim.")
    else:
        await msg.reply_text(
            f"⚠️ Gagal stop node.\n<code>{proc.stderr}</code>",
            parse_mode=ParseMode.HTML,
        )


async def create_swap(msg: Message, size_gb: int) -> None:
    await msg.reply_text(
        f"💾 Membuat swap baru <b>{size_gb}G</b>…\n"
        f"Swap aktif sekarang:\n<code>{get_swap_status()}</code>",
        parse_mode=ParseMode.HTML,
    )

    cmd = f"""
set -e
swapoff -a || true
rm -f {SWAPFILE}
if ! fallocate -l {size_gb}G {SWAPFILE}; then
  dd if=/dev/zero of={SWAPFILE} bs=1G count={size_gb} status=progress
fi
chmod 600 {SWAPFILE}
mkswap {SWAPFILE}
swapon {SWAPFILE}
cp /etc/fstab /etc/fstab.bak_deklan_swap || true
if grep -q '^{SWAPFILE}' /etc/fstab 2>/dev/null; then
  sed -i 's|^{SWAPFILE}.*|{SWAPFILE} none swap sw 0 0|' /etc/fstab
else
  echo '{SWAPFILE} none swap sw 0 0' >> /etc/fstab
fi
"""

    proc = run_cmd(cmd, timeout=180)
    ok = proc.returncode == 0

    append_swap_log(
        {
            "ts": datetime.utcnow().isoformat() + "Z",
            "action": "create",
            "size_gb": size_gb,
            "ok": ok,
            "stderr": proc.stderr[-4000:],
        }
    )

    if ok:
        await msg.reply_text(
            f"✅ Swap {size_gb}G aktif.\n\n"
            f"Status baru:\n<code>{get_swap_status()}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await msg.reply_text(
            "❌ Gagal membuat swap.\n"
            f"<code>{proc.stderr[-4000:]}</code>",
            parse_mode=ParseMode.HTML,
        )


async def remove_swap(msg: Message) -> None:
    await msg.reply_text("❌ Menghapus swap & menonaktifkan…")
    cmd = f"""
swapoff -a || true
rm -f {SWAPFILE}
cp /etc/fstab /etc/fstab.bak_deklan_swap_remove || true
sed -i '\\|{SWAPFILE} none swap sw 0 0|d' /etc/fstab || true
"""
    proc = run_cmd(cmd, timeout=120)
    ok = proc.returncode == 0
    append_swap_log(
        {
            "ts": datetime.utcnow().isoformat() + "Z",
            "action": "remove",
            "ok": ok,
            "stderr": proc.stderr[-4000:],
        }
    )
    if ok:
        await msg.reply_text("✅ Swap dihapus. Sekarang:\n" + get_swap_status())
    else:
        await msg.reply_text(
            "⚠️ Gagal hapus swap.\n"
            f"<code>{proc.stderr[-4000:]}</code>",
            parse_mode=ParseMode.HTML,
        )


async def clean_vps(msg: Message) -> None:
    await msg.reply_text(
        "🧹 <b>Clean VPS</b> dimulai…\n"
        "• Stop container tidak terpakai\n"
        "• Docker prune\n"
        "• Bersihkan log & tmp\n"
        "• apt autoremove + clean",
        parse_mode=ParseMode.HTML,
    )
    cmd = r"""
set -e
docker ps -q >/dev/null 2>&1 && docker stop $(docker ps -aq) || true
docker system prune -af --volumes || true

rm -rf /var/tmp/* /tmp/* || true

journalctl --rotate || true
journalctl --vacuum-size=200M || true

apt-get autoremove -y || true
apt-get clean || true
"""

    proc = run_cmd(cmd, timeout=600)
    if proc.returncode == 0:
        await msg.reply_text("✅ Clean VPS selesai.")
    else:
        await msg.reply_text(
            "⚠️ Clean VPS kena error (cek log manual).\n"
            f"<code>{proc.stderr[-4000:]}</code>",
            parse_mode=ParseMode.HTML,
        )


async def install_node(msg: Message) -> None:
    installer = FUSION_DIR / "install.sh"
    if not installer.is_file():
        await msg.reply_text(
            f"⚠️ File installer tidak ditemukan:\n<code>{installer}</code>",
            parse_mode=ParseMode.HTML,
        )
        return
    await msg.reply_text(
        "📦 Menjalankan installer node…\n"
        f"<code>{installer}</code>\n\nIni bisa makan waktu beberapa menit.",
        parse_mode=ParseMode.HTML,
    )
    cmd = f"bash {shlex.quote(str(installer))}"
    proc = run_cmd(cmd, timeout=3600)
    if proc.returncode == 0:
        await msg.reply_text("✅ Installer selesai tanpa error (cek log untuk detail).")
    else:
        await msg.reply_text(
            "❌ Installer gagal (cek error di bawah & di VPS).\n"
            f"<code>{proc.stderr[-4000:]}</code>",
            parse_mode=ParseMode.HTML,
        )


async def monitor_now(msg: Message) -> None:
    """
    Monitor cepat:
    - cek status service
    - scan error terakhir di log RL-Swarm
    """
    await msg.reply_text("📊 Running quick monitor…")

    log_path = RL_DIR / "logs" / "swarm_launcher.log"
    err_snippet = "Log tidak ditemukan."
    if log_path.is_file():
        try:
            tail = run_cmd(f"tail -n 60 {shlex.quote(str(log_path))}")
            text = tail.stdout
            # cari line yang mengandung "Error" / "Exception"
            lines = [
                ln
                for ln in text.splitlines()
                if any(
                    token in ln
                    for token in ["Error", "Exception", "Traceback", "ConnectionRefused"]
                )
            ]
            if lines:
                err_snippet = "\n".join(lines[-10:])
            else:
                err_snippet = "Tidak ada error jelas di 60 baris terakhir."
        except Exception as e:
            err_snippet = f"Gagal baca log: {e}"

    node_status = run_cmd(f"systemctl is-active {shlex.quote(SERVICE_NAME)}")
    active = node_status.stdout.strip() or "unknown"

    msg_text = (
        f"📊 <b>Quick Monitor</b>\n"
        f"Service: <code>{SERVICE_NAME}</code> → <b>{active}</b>\n\n"
        f"🔍 Error snippet terakhir:\n"
        f"<code>{err_snippet}</code>"
    )
    await msg.reply_text(msg_text, parse_mode=ParseMode.HTML)


async def view_logs(msg: Message) -> None:
    log_path = RL_DIR / "logs" / "swarm_launcher.log"
    if not log_path.is_file():
        await msg.reply_text(
            f"⚠️ Log tidak ditemukan: <code>{log_path}</code>",
            parse_mode=ParseMode.HTML,
        )
        return
    tail = run_cmd(f"tail -n 60 {shlex.quote(str(log_path))}")
    await msg.reply_text(
        "📄 <b>Tail 60 baris terakhir</b>:\n"
        f"<code>{tail.stdout[-3800:]}</code>",
        parse_mode=ParseMode.HTML,
    )


async def kill_python(msg: Message) -> None:
    await msg.reply_text("💀 Kill semua proses python (kecuali bot)…")
    cmd = r"""
for pid in $(ps axo pid,cmd | grep python | grep -v 'telegram' | grep -v 'bot.py' | grep -v grep | awk '{print $1}'); do
  kill -9 "$pid" || true
done
"""
    proc = run_cmd(cmd)
    if proc.returncode == 0:
        await msg.reply_text("✅ Semua proses python non-bot dicoba kill.")
    else:
        await msg.reply_text(
            "⚠️ Kill python error (cek manual).\n"
            f"<code>{proc.stderr[-4000:]}</code>",
            parse_mode=ParseMode.HTML,
        )


async def fix_docker(msg: Message) -> None:
    await msg.reply_text("🐳 Mencoba perbaiki Docker (restart + prune)…")
    cmd = r"""
systemctl restart docker || true
docker system prune -af --volumes || true
"""
    proc = run_cmd(cmd, timeout=600)
    if proc.returncode == 0:
        await msg.reply_text("✅ Docker direstart & dipruned.")
    else:
        await msg.reply_text(
            "⚠️ Docker fix ada error.\n"
            f"<code>{proc.stderr[-4000:]}</code>",
            parse_mode=ParseMode.HTML,
        )


async def delete_rlswarm(msg: Message) -> None:
    await msg.reply_text(
        f"🗑 Menghapus folder RL-Swarm:\n<code>{RL_DIR}</code>\n"
        "Service akan <b>stop</b> dulu.",
        parse_mode=ParseMode.HTML,
    )
    cmd = f"""
systemctl stop {shlex.quote(SERVICE_NAME)} || true
rm -rf {shlex.quote(str(RL_DIR))}
"""
    proc = run_cmd(cmd)
    if proc.returncode == 0:
        await msg.reply_text("✅ RL-Swarm folder dihapus.")
    else:
        await msg.reply_text(
            "⚠️ Gagal hapus RL-Swarm.\n"
            f"<code>{proc.stderr[-4000:]}</code>",
            parse_mode=ParseMode.HTML,
        )


async def check_update(msg: Message) -> None:
    await msg.reply_text("🆕 Checking update deklan-fusion…")
    cmd_local = f"cd {shlex.quote(str(FUSION_DIR))} && git rev-parse HEAD"
    cmd_remote = (
        f"cd {shlex.quote(str(FUSION_DIR))} && "
        "git ls-remote origin -h refs/heads/main | awk '{print $1}'"
    )
    local = run_cmd(cmd_local)
    remote = run_cmd(cmd_remote)

    if local.returncode != 0 or remote.returncode != 0:
        await msg.reply_text(
            "⚠️ Tidak bisa cek update (cek koneksi / git remote).",
        )
        return

    local_sha = local.stdout.strip()
    remote_sha = remote.stdout.strip()

    if local_sha == remote_sha:
        await msg.reply_text("✅ Sudah versi terbaru (main == origin/main).")
    else:
        await msg.reply_text(
            "🆕 <b>Update tersedia!</b>\n\n"
            "Jalankan di VPS:\n"
            f"<code>cd {FUSION_DIR} && git pull && systemctl restart deklan-fusion-bot</code>",
            parse_mode=ParseMode.HTML,
        )


# ======================================================================
# DOCUMENT UPLOAD (KEYS)
# ======================================================================


KEY_MAP = {
    "swarm.pem": "swarm.pem",
    "userApiKey.json": "userApiKey.json",
    "userData.json": "userData.json",
}


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update, context):
        return
    msg = update.effective_message
    doc = msg.document
    if not doc:
        return

    filename = doc.file_name or ""
    filename = filename.strip()

    if filename not in KEY_MAP:
        await msg.reply_text(
            "🗝 Nama file tidak dikenali.\n"
            "Gunakan salah satu nama berikut:\n"
            "• swarm.pem\n"
            "• userApiKey.json\n"
            "• userData.json",
        )
        return

    KEY_DIR.mkdir(parents=True, exist_ok=True)
    dest = KEY_DIR / KEY_MAP[filename]

    # backup kalau sudah ada
    if dest.exists():
        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        backup = dest.with_suffix(dest.suffix + f".bak-{ts}")
        dest.rename(backup)

    file = await doc.get_file()
    await file.download_to_drive(custom_path=str(dest))

    await msg.reply_text(
        f"✅ File <code>{filename}</code> disimpan ke:\n"
        f"<code>{dest}</code>",
        parse_mode=ParseMode.HTML,
    )


# ======================================================================
# MAIN APP
# ======================================================================


def build_app() -> Application:
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    app.add_handler(CommandHandler(["start", "menu", "help"], start))
    app.add_handler(CallbackQueryHandler(handle_menu_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    return app


def main() -> None:
    app = build_app()
    app.run_polling(
        allowed_updates=["message", "callback_query", "edited_message", "channel_post"]
    )


if __name__ == "__main__":
    main()
