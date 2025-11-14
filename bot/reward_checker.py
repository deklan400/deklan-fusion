import os
import json
import logging
from bot.ssh_client import SSHClient

logger = logging.getLogger(__name__)

DB_PATH = "/opt/deklan-fusion/fusion_db.json"


# ======================================
# DATABASE
# ======================================
def load_db():
    """Load database dari JSON file."""
    if not os.path.exists(DB_PATH):
        return {"vps": {}}

    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"vps": {}}


def save_db(db):
    """Save database ke JSON file."""
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=4)


# ======================================
# PARSE REWARD LOGS
# ======================================
def check_reward(ip, username, password):
    """
    Check reward dan score dari VPS.
    Return dict:
    {
        "label": 1,
        "peer": "Qmxxx",
        "status": "online/offline",
        "score": "800 (+25)",
        "reward": "3085 (+225)",
        "points": "N/A (+0)"
    }
    """

    # Load DB
    db = load_db()
    vps_data = db["vps"].get(ip, {})
    last = vps_data.get("last", {})

    # Old values
    old_reward = last.get("reward")
    old_score = last.get("score")
    old_points = last.get("points")

    # Label (index VPS)
    all_ips = list(db["vps"].keys())
    label = all_ips.index(ip) + 1 if ip in all_ips else 0

    # Read logs
    success, output = SSHClient.execute(
        ip, username, password,
        "tail -n 200 /root/rl-swarm/logs/swarm_launcher.log 2>/dev/null || echo ''"
    )

    if not success:
        return {
            "label": label,
            "peer": "N/A",
            "status": "offline",
            "score": "N/A",
            "reward": "N/A",
            "points": "N/A"
        }

    # Parse values
    def extract(pattern):
        ok, out = SSHClient.execute(
            ip, username, password,
            f"grep -o \"{pattern}\" /root/rl-swarm/logs/swarm_launcher.log | tail -1"
        )
        return out.strip() if ok and out.strip() else None

    new_score = extract("score: [0-9\\.]*")
    new_reward = extract("reward: [0-9\\.]*")
    new_points = extract("points: [0-9\\.]*")
    peer_id = extract("Qm[a-zA-Z0-9]\\{44,\\}")

    # Clean numeric
    if new_score and "score:" in new_score:
        new_score = new_score.split(":")[1].strip()
    if new_reward and "reward:" in new_reward:
        new_reward = new_reward.split(":")[1].strip()
    if new_points and "points:" in new_points:
        new_points = new_points.split(":")[1].strip()

    # Online status
    ok, st = SSHClient.execute(
        ip, username, password,
        "systemctl is-active rl-swarm.service 2>/dev/null || echo inactive"
    )
    status = "online" if ok and "active" in st else "offline"

    # Format delta
    def delta(new, old):
        if not new:
            return "N/A"
        try:
            newf = float(new)
            if old:
                oldf = float(old)
                d = newf - oldf
                return f"{int(newf)} (+{int(d)})" if d >= 0 else f"{int(newf)} ({int(d)})"
            return f"{int(newf)}"
        except:
            return new

    score_str = delta(new_score, old_score)
    reward_str = delta(new_reward, old_reward)
    points_str = delta(new_points, old_points)

    # Save back to DB
    db["vps"].setdefault(ip, {})
    db["vps"][ip]["last"] = {
        "score": new_score,
        "reward": new_reward,
        "points": new_points,
        "peer_id": peer_id or "N/A"
    }
    save_db(db)

    return {
        "label": label,
        "peer": peer_id or "N/A",
        "status": status,
        "score": score_str,
        "reward": reward_str,
        "points": points_str
    }


# ======================================
# CHECK ALL VPS
# ======================================
def check_all_rewards():
    db = load_db()
    results = []

    for ip, info in db["vps"].items():
        username = info.get("user", "root")
        password = info.get("password", "")
        res = check_reward(ip, username, password)
        results.append(res)

    return results
