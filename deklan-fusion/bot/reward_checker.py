"""
Reward Checker untuk parse logs dan hitung delta (score, reward, points).
"""
import re
import json
import os
import sys
import logging
from typing import Dict, Optional, Tuple

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from ssh_client import SSHClient

logger = logging.getLogger(__name__)

DB_PATH = "/opt/deklan-fusion/fusion_db.json"
LOG_PATH = "/root/rl-swarm/logs/swarm_launcher.log"


def load_db() -> dict:
    """Load database dari JSON file."""
    if not os.path.exists(DB_PATH):
        return {"vps": {}, "keys": {}}
    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading DB: {e}")
        return {"vps": {}, "keys": {}}


def save_db(data: dict):
    """Save database ke JSON file."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)


def parse_log_line(line: str) -> Dict[str, Optional[str]]:
    """
    Parse satu baris log untuk extract reward, score, points, peer ID.
    
    Returns:
        Dict dengan keys: reward, score, points, peer_id
    """
    result = {
        "reward": None,
        "score": None,
        "points": None,
        "peer_id": None
    }
    
    # Pattern untuk reward
    reward_match = re.search(r'reward[:\s]+([0-9.]+)', line, re.IGNORECASE)
    if reward_match:
        result["reward"] = reward_match.group(1)
    
    # Pattern untuk score
    score_match = re.search(r'score[:\s]+([0-9.]+)', line, re.IGNORECASE)
    if score_match:
        result["score"] = score_match.group(1)
    
    # Pattern untuk points
    points_match = re.search(r'points[:\s]+([0-9.]+)', line, re.IGNORECASE)
    if points_match:
        result["points"] = points_match.group(1)
    
    # Pattern untuk peer ID (Qm... atau format lain)
    peer_match = re.search(r'(Qm[a-zA-Z0-9]{44,})', line)
    if peer_match:
        result["peer_id"] = peer_match.group(1)
    
    return result


def get_latest_values_from_log(log_content: str) -> Dict[str, Optional[str]]:
    """
    Parse log content untuk dapatkan nilai terbaru.
    
    Args:
        log_content: Content dari log file
        
    Returns:
        Dict dengan latest values: reward, score, points, peer_id
    """
    lines = log_content.split('\n')
    latest = {
        "reward": None,
        "score": None,
        "points": None,
        "peer_id": None
    }
    
    # Parse dari belakang (latest first)
    for line in reversed(lines):
        parsed = parse_log_line(line)
        for key in latest:
            if parsed[key] and not latest[key]:
                latest[key] = parsed[key]
    
    return latest


def check_reward(ip: str, username: str, password: str) -> Dict:
    """
    Check reward untuk satu VPS.
    
    Args:
        ip: IP address VPS
        username: SSH username
        password: SSH password
        
    Returns:
        Dict dengan struktur:
        {
            "label": n,
            "peer": "xxxxxx",
            "status": "online/offline",
            "score": "800 (+25)",
            "reward": "3085 (+225)",
            "points": "N/A (+0)"
        }
    """
    db = load_db()
    
    # Get last values dari database (support both old and new format)
    vps_data = {}
    if "vps" in db and ip in db["vps"]:
        # Old format
    vps_data = db["vps"].get(ip, {})
    else:
        # New format - search in all users
        for user_id, user_data in db.get("users", {}).items():
            if ip in user_data.get("vps", {}):
                vps_data = user_data["vps"][ip]
                break
    
    last_data = vps_data.get("last", {})
    old_reward = last_data.get("reward")
    old_score = last_data.get("score")
    old_points = last_data.get("points")
    
    # Get label (find IP in all users' VPS lists)
    label = 0
    all_vps = []
    if "vps" in db:
        # Old format
        all_vps = list(db["vps"].keys())
    else:
        # New format - collect all VPS from all users
        for user_data in db.get("users", {}).values():
            all_vps.extend(list(user_data.get("vps", {}).keys()))
    
    if ip in all_vps:
        label = all_vps.index(ip) + 1
    
    # SSH ke VPS untuk get logs
    success, output = SSHClient.execute(
        ip, username, password,
        "tail -n 200 /root/rl-swarm/logs/swarm_launcher.log 2>/dev/null || echo ''"
    )
    
    if not success:
        # VPS offline atau error
        return {
            "label": label,
            "peer": "N/A",
            "status": "offline",
            "score": "N/A",
            "reward": "N/A",
            "points": "N/A"
        }
    
    # Parse log untuk dapatkan latest values
    latest = get_latest_values_from_log(output)
    
    # Check service status
    status_success, status_output = SSHClient.execute(
        ip, username, password,
        "systemctl is-active rl-swarm.service 2>/dev/null || echo 'inactive'"
    )
    
    is_online = status_success and "active" in status_output.lower()
    status = "online" if is_online else "offline"
    
    # Calculate deltas
    def format_with_delta(new_val: Optional[str], old_val: Optional[str]) -> str:
        if not new_val:
            return "N/A"
        
        try:
            new_float = float(new_val)
            if old_val:
                old_float = float(old_val)
                delta = new_float - old_float
                if delta > 0:
                    return f"{int(new_float)} (+{int(delta)})"
                elif delta < 0:
                    return f"{int(new_float)} ({int(delta)})"
                else:
                    return f"{int(new_float)} (+0)"
            else:
                return f"{int(new_float)}"
        except:
            return new_val
    
    score_str = format_with_delta(latest["score"], old_score)
    reward_str = format_with_delta(latest["reward"], old_reward)
    points_str = format_with_delta(latest["points"], old_points)
    
    # Update database dengan latest values (find which user owns this VPS)
    if "vps" in db and ip in db["vps"]:
        # Old format
    if ip not in db["vps"]:
        db["vps"][ip] = {}
    db["vps"][ip]["last"] = {
        "reward": latest["reward"],
        "score": latest["score"],
        "points": latest["points"],
        "peer_id": latest["peer_id"]
    }
    else:
        # New format - find user who owns this VPS
        for user_id, user_data in db.get("users", {}).items():
            if ip in user_data.get("vps", {}):
                if "last" not in user_data["vps"][ip]:
                    user_data["vps"][ip]["last"] = {}
                user_data["vps"][ip]["last"] = {
                    "reward": latest["reward"],
                    "score": latest["score"],
                    "points": latest["points"],
                    "peer_id": latest["peer_id"]
                }
                break
    
    save_db(db)
    
    return {
        "label": label,
        "peer": latest["peer_id"] or "N/A",
        "status": status,
        "score": score_str,
        "reward": reward_str,
        "points": points_str
    }


def check_all_rewards(user_id: int = None) -> list:
    """
    Check rewards untuk semua VPS.
    
    Args:
        user_id: Optional user ID to filter VPS. If None, check all VPS (for monitor).
    
    Returns:
        List of reward dicts untuk setiap VPS
    """
    db = load_db()
    results = []
    
    if user_id:
        # Check only user's VPS
        from actions import get_user_vps_list
        vps_list = get_user_vps_list(db, user_id)
        for ip, vps_data in vps_list.items():
            username = vps_data.get("user", "root")
            password = vps_data.get("password", "")
            result = check_reward(ip, username, password)
            results.append(result)
    else:
        # Check all VPS (for monitor - backward compatible)
        if "vps" in db:
            # Old format
    for ip, vps_data in db["vps"].items():
        username = vps_data.get("user", "root")
        password = vps_data.get("password", "")
                result = check_reward(ip, username, password)
                results.append(result)
        else:
            # New format - check all users' VPS
            for user_data in db.get("users", {}).values():
                for ip, vps_data in user_data.get("vps", {}).items():
                    username = vps_data.get("user", "root")
                    password = vps_data.get("password", "")
        result = check_reward(ip, username, password)
        results.append(result)
    
    return results

