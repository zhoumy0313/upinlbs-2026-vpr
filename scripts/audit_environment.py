#!/usr/bin/env python3
"""Read-only hardware/service audit; never print credentials or proxy values."""
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from urllib.parse import urlsplit


def command(argv):
    print("\n$ " + " ".join(argv), flush=True)
    if not shutil.which(argv[0]):
        print("not installed (exit_status=127)")
        return
    result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    print(result.stdout + result.stderr)
    print("exit_status=" + str(result.returncode))


print("platform:", platform.platform(), "python:", sys.version, "executable:", sys.executable)
for argv in [
    ["cat", "/etc/os-release"], ["uname", "-r"], ["lscpu"], ["free", "-h"],
    ["df", "-h", "."], ["lspci"],
    ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.free,compute_cap", "--format=csv"],
    ["systemctl", "is-active", "ssh"], ["ssh", "-V"],
    ["pgrep", "-x", "FlClash"], ["pgrep", "-x", "FlClashCore"],
    ["codex", "--version"], ["codex", "login", "status"], ["git", "--version"],
]:
    command(argv)
proxy_names = ["http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "no_proxy"]
print("\nproxy variable presence only:", json.dumps({name: bool(os.getenv(name)) for name in proxy_names}))
for name in proxy_names[:6]:
    value = os.getenv(name)
    if not value:
        continue
    parsed = urlsplit(value)
    try:
        with socket.create_connection((parsed.hostname, parsed.port or 80), timeout=5):
            print(name, "proxy TCP reachable (address omitted)")
    except (OSError, ValueError) as exc:
        print(name, "proxy TCP unavailable:", type(exc).__name__)
for host in ["github.com", "download.pytorch.org", "pypi.org"]:
    try:
        socket.getaddrinfo(host, 443)
        print(host, "DNS resolution OK")
    except OSError as exc:
        print(host, "DNS resolution failed:", type(exc).__name__)
