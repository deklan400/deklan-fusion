import re

# Error patterns we want to detect
ERROR_PATTERNS = {
    "connection_refused": r"ConnectionRefusedError",
    "file_not_found": r"FileNotFoundError",
    "uvloop_error": r"uvloop\.error",
    "dht_error": r"DHT.*(timeout|fail|error)",
    "gpu_fail": r"CUDA.*(fail|error)",
}


def parse_errors(log_text: str):
    """Check log text for known error patterns"""
    detected = []

    for key, pattern in ERROR_PATTERNS.items():
        if re.search(pattern, log_text, re.IGNORECASE):
            detected.append(key)

    return detected
