# 🔥 Deklan Fusion

Multi-VPS Manager untuk Gensyn RL-Swarm Nodes via Telegram Bot.

## 📋 Fitur

- ✅ **Multi-VPS Management** - Kelola banyak VPS dari satu bot
- ✅ **Auto Key Sync** - Upload keys (swarm.pem, userApiKey.json, userData.json) dan auto-sync ke semua VPS
- ✅ **Node Control** - Start, Stop, Restart, Status, dan Logs untuk setiap node
- ✅ **Change Report** - Auto-generate report setiap 3 jam dengan delta score, reward, dan points
- ✅ **Reward Tracking** - Track reward, score, dan points untuk setiap VPS
- ✅ **Swap Management** - Create/remove swap (32G, 50G, 80G, 100G) via bot
- ✅ **VPS Cleanup** - Clean VPS dengan satu command
- ✅ **Node Update** - Update node ke versi terbaru

## 🚀 Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd deklan-fusion
```

### 2. Run Install Script dengan Token

Install script sekarang menerima token sebagai command-line arguments:

```bash
sudo bash install.sh --token YOUR_BOT_TOKEN --admin-chat-id YOUR_CHAT_ID [--admin-id YOUR_ADMIN_ID]
```

**Contoh:**
```bash
sudo bash install.sh --token 123456789:ABCdefGHIjklMNOpqrsTUVwxyz --admin-chat-id 123456789 --admin-id 987654321
```

**Cara dapatkan BOT_TOKEN:**
1. Chat dengan [@BotFather](https://t.me/BotFather) di Telegram
2. Kirim `/newbot` dan ikuti instruksi
3. Copy token yang diberikan

**Cara dapatkan CHAT_ID:**
1. Chat dengan [@userinfobot](https://t.me/userinfobot)
2. Copy ID yang diberikan

Script akan:
- Membuat direktori `/opt/deklan-fusion`
- Install Python dependencies
- Setup systemd services dengan token yang diberikan
- Enable bot dan monitor timer

**Note:** Token dan credentials tidak disimpan di repository. Semua data sensitif dikonfigurasi via command-line arguments saat instalasi.

### 🔒 Public Bot - Multi-User System

Bot ini **AMAN untuk digunakan secara public** seperti bot monitoring lainnya. Sistem menggunakan **user isolation** - setiap user hanya bisa manage VPS mereka sendiri.

**Cara Kerja:**
1. Setiap user bisa add VPS mereka sendiri dengan `/addvps IP USER PASS`
2. User hanya bisa melihat dan control VPS yang mereka add
3. Keys yang di-upload juga terisolasi per user
4. Tidak ada user yang bisa akses VPS user lain

**Semua Fitur Bisa Digunakan Public:**
- `/addvps IP USER PASS` - Tambah VPS Anda sendiri
- `/removevps IP` - Hapus VPS Anda
- `/listvps` - List VPS Anda
- `🔑 Upload Keys` - Upload keys Anda (auto-sync ke VPS Anda)
- `🚀 Start Node` - Start semua node Anda
- `🔄 Restart Node` - Restart semua node Anda
- `🟢 Node Status` - Check status VPS Anda
- `📈 Check Reward` - Check reward VPS Anda
- `📡 Peer Checker` - Check peer ID VPS Anda
- `📊 Node Info` - Info lengkap node Anda
- `💾 Swap Menu` - Create/remove swap di VPS Anda
- `🧹 Clean VPS` - Clean VPS Anda
- `⚙ Update Node` - Update node di VPS Anda

**Keamanan:**
- ✅ User isolation - setiap user hanya akses VPS mereka sendiri
- ✅ Ownership check - semua operasi verify ownership sebelum execute
- ✅ Keys terisolasi - keys disimpan per user, tidak bisa diakses user lain
- ✅ Database structure - data terpisah per user ID

### 3. Start Services

```bash
# Start bot
sudo systemctl start fusion-bot

# Start monitor timer (runs every 3 hours)
sudo systemctl start fusion-monitor.timer

# Enable on boot
sudo systemctl enable fusion-bot
sudo systemctl enable fusion-monitor.timer
```

### 5. Check Status

```bash
# Check bot status
sudo systemctl status fusion-bot

# Check monitor status
sudo systemctl status fusion-monitor

# View logs
sudo journalctl -u fusion-bot -f
sudo journalctl -u fusion-monitor -f
```

## 📱 Usage

### Commands

- `/start` - Start bot dan tampilkan menu
- `/addvps IP USER PASS` - Tambah VPS baru
- `/removevps IP` - Hapus VPS
- `/listvps` - List semua VPS
- `/menu` - Tampilkan menu

### Upload Keys

Kirim file berikut ke bot:
- `swarm.pem`
- `userApiKey.json`
- `userData.json`

Bot akan otomatis sync ke semua VPS.

### Menu Buttons

- **🖥 VPS Connect** - Manage VPS (Add, List, Remove)
- **🔑 Upload Keys** - Upload keys untuk node
- **🟢 Node Status** - Check status semua node
- **📈 Check Reward** - Check reward report sekarang
- **💾 Swap Menu** - Create/remove swap
- **🧹 Clean VPS** - Clean semua VPS
- **⚙ Update Node** - Update node ke versi terbaru

### VPS Control Panel

Setelah memilih VPS dari list:
- **🟢 Status** - Lihat status lengkap node
- **▶️ Start** - Start node
- **🔄 Restart** - Restart node
- **🛑 Stop** - Stop node
- **📄 Logs** - Lihat logs (last 60 lines)

## 📊 Change Report

Monitor akan otomatis generate change report setiap 3 jam dengan format:

```
🔥 CHANGE REPORT (3 HOURS)

Label : 1
Peer  : Qmxxxxxxx
🟢
Score : 800 (+25)
Reward : 3085 (+225)
Point  : N/A(+0)

Label : 2
Peer  : Qmyyyyyyy
🔴
Score : 650
Reward : 2100
Point  : N/A

Bot created by Deklan
```

## 📁 Project Structure

```
deklan-fusion/
├── bot/
│   ├── __init__.py
│   ├── bot.py              # Main bot application
│   ├── handlers.py         # Message & callback handlers
│   ├── actions.py          # VPS actions (add, remove, control)
│   ├── ssh_client.py       # SSH wrapper
│   ├── file_receiver.py    # File upload handler
│   ├── reward_checker.py   # Reward/score parser
│   ├── keyboard.py        # Keyboard layouts
│   ├── config.py          # Configuration
│   ├── utils.py           # Utility functions
│   └── requirements.txt   # Python dependencies
├── monitor/
│   ├── __init__.py
│   ├── monitor.py         # Monitor daemon
│   └── parser.py          # Log parser
├── scripts/
│   ├── setup_vps.sh       # One-command VPS setup
│   ├── move_to_vps.sh     # Move to new VPS
│   ├── create_swap.sh     # Create swap
│   ├── update_node.sh     # Update node
│   └── ...
├── etc/
│   └── systemd/
│       ├── fusion-bot.service
│       ├── fusion-monitor.service
│       └── fusion-monitor.timer
├── install.sh             # Installation script
└── README.md
```

## 🔧 Configuration

Database disimpan di `/opt/deklan-fusion/fusion_db.json` dengan struktur multi-user (setiap user terisolasi):

```json
{
  "users": {
    "123456789": {
      "vps": {
        "1.2.3.4": {
          "user": "root",
          "password": "password",
          "last": {
            "reward": "3085",
            "score": "800",
            "points": null,
            "peer_id": "Qmxxxxxxx"
          }
        }
      },
      "keys": {
        "swarm.pem": "/opt/deklan-fusion/keys/123456789/swarm.pem",
        "userApiKey.json": "/opt/deklan-fusion/keys/123456789/userApiKey.json",
        "userData.json": "/opt/deklan-fusion/keys/123456789/userData.json"
      }
    },
    "987654321": {
      "vps": {
        "5.6.7.8": {
          "user": "root",
          "password": "password2"
        }
      },
      "keys": {}
    }
  }
}
```

**Struktur:**
- `users` - Container untuk semua user
- `users[USER_ID]` - Data untuk user tertentu (USER_ID = Telegram User ID)
- `users[USER_ID].vps` - Daftar VPS milik user tersebut
- `users[USER_ID].keys` - Keys milik user tersebut

**Isolasi:**
- Setiap user hanya bisa akses VPS dan keys mereka sendiri
- Keys disimpan di folder terpisah: `/opt/deklan-fusion/keys/{USER_ID}/`
- Tidak ada user yang bisa akses data user lain

## 🛠 Troubleshooting

### Bot tidak start

```bash
# Check logs
sudo journalctl -u fusion-bot -n 50

# Check systemd service configuration
sudo systemctl cat fusion-bot

# Restart service
sudo systemctl restart fusion-bot
```

### Update Token/Configuration

Jika perlu update token atau konfigurasi:

```bash
# Edit systemd service file
sudo systemctl edit fusion-bot --full

# Atau re-run install script dengan parameter baru
sudo bash install.sh --token NEW_TOKEN --admin-chat-id NEW_CHAT_ID

# Reload dan restart
sudo systemctl daemon-reload
sudo systemctl restart fusion-bot
```

### Monitor tidak jalan

```bash
# Check timer status
sudo systemctl status fusion-monitor.timer

# Check service status
sudo systemctl status fusion-monitor

# Manually trigger
sudo systemctl start fusion-monitor
```

### SSH connection failed

- Pastikan VPS bisa diakses via SSH
- Check username dan password
- Pastikan firewall tidak block port 22

## 📝 License

See LICENSE file.

## 👤 Author

Bot created by Deklan


