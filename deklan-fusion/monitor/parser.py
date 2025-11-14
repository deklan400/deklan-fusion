"""
Parser untuk extract data dari logs.
"""
import re
from typing import Dict, Optional


def parse_peer_id(log_content: str) -> Optional[str]:
    """
    Parse peer ID dari log content.
    
    Args:
        log_content: Content dari log file
        
    Returns:
        Peer ID atau None jika tidak ditemukan
    """
    # Pattern untuk peer ID (Qm... format)
    pattern = r'(Qm[a-zA-Z0-9]{44,})'
    match = re.search(pattern, log_content)
    
    if match:
        return match.group(1)
    
    return None


def parse_reward(log_content: str) -> Optional[float]:
    """
    Parse reward value dari log content.
    
    Args:
        log_content: Content dari log file
        
    Returns:
        Reward value atau None jika tidak ditemukan
    """
    # Pattern untuk reward
    patterns = [
        r'reward[:\s]+([0-9.]+)',
        r'reward\s*=\s*([0-9.]+)',
        r'"reward"\s*:\s*([0-9.]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, log_content, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except:
                continue
    
    return None


def parse_score(log_content: str) -> Optional[float]:
    """
    Parse score value dari log content.
    
    Args:
        log_content: Content dari log file
        
    Returns:
        Score value atau None jika tidak ditemukan
    """
    # Pattern untuk score
    patterns = [
        r'score[:\s]+([0-9.]+)',
        r'score\s*=\s*([0-9.]+)',
        r'"score"\s*:\s*([0-9.]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, log_content, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except:
                continue
    
    return None


def parse_points(log_content: str) -> Optional[float]:
    """
    Parse points value dari log content.
    
    Args:
        log_content: Content dari log file
        
    Returns:
        Points value atau None jika tidak ditemukan
    """
    # Pattern untuk points
    patterns = [
        r'points[:\s]+([0-9.]+)',
        r'points\s*=\s*([0-9.]+)',
        r'"points"\s*:\s*([0-9.]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, log_content, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except:
                continue
    
    return None


def parse_all(log_content: str) -> Dict[str, Optional[str]]:
    """
    Parse semua values dari log content.
    
    Args:
        log_content: Content dari log file
        
    Returns:
        Dict dengan keys: peer_id, reward, score, points
    """
    return {
        "peer_id": parse_peer_id(log_content),
        "reward": str(parse_reward(log_content)) if parse_reward(log_content) else None,
        "score": str(parse_score(log_content)) if parse_score(log_content) else None,
        "points": str(parse_points(log_content)) if parse_points(log_content) else None
    }


