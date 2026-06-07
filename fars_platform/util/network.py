"""Network helpers for the API server."""
from __future__ import annotations

import socket
import time
import urllib.error
import urllib.request


def find_free_port(host: str = "127.0.0.1", start: int = 8080, end: int = 8099) -> int:
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No free port on {host} in range {start}-{end}")


def wait_for_server(host: str, port: int, timeout: float = 15.0) -> bool:
    url = f"http://{host}:{port}/api/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            time.sleep(0.25)
    return False
