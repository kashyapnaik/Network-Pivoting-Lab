#!/usr/bin/env python3
"""
lab_config.py — shared configuration, logging, and SAFETY GUARD for the
Network Pivoting Lab automation framework.

Every script imports from here so that:
  * lab hosts/credentials live in exactly one place, and
  * no script can ever act against a target outside the isolated lab.

The safety guard (assert_lab_target) refuses any IP that is not inside the
two lab subnets. Import it and call it before you scan/attack anything.
"""

import ipaddress
import logging
import os
from datetime import datetime

# ---------------------------------------------------------------------------
# Lab definition (edit here if you rebuild with different addressing)
# ---------------------------------------------------------------------------
DMZ_NET = "172.16.10.0/24"
INTERNAL_NET = "10.0.0.0/24"

HOSTS = {
    "kali":   "172.16.10.5",    # attacker (DMZ)
    "pivot_dmz":      "172.16.10.15",  # pivot, DMZ side
    "pivot_internal": "10.0.0.15",     # pivot, internal side
    "windows":        "10.0.0.25",     # internal target
}

# SOCKS proxy exposed on the attacker by the reverse Chisel tunnel
SOCKS_HOST = "127.0.0.1"
SOCKS_PORT = 1080

# Chisel tunnel
CHISEL_SERVER_PORT = 8080

# LAB-ONLY credentials (deliberately weak; created only for this lab).
# Never put real/production credentials here.
LAB_CREDS = {"username": "labadmin", "password": "Lab@12345"}

# The ONLY networks any script in this framework is allowed to touch.
_ALLOWED_NETS = [ipaddress.ip_network(DMZ_NET), ipaddress.ip_network(INTERNAL_NET)]

# ---------------------------------------------------------------------------
# Logging — every script logs to scripts/../logs/<name>.log and the console
# ---------------------------------------------------------------------------
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")


def get_logger(name: str) -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(os.path.join(LOG_DIR, f"{name}.log"))
    fh.setFormatter(fmt)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


# ---------------------------------------------------------------------------
# SAFETY GUARD — call this before touching any target
# ---------------------------------------------------------------------------
class OutOfScopeError(Exception):
    """Raised when a target is not inside the isolated lab networks."""


def is_lab_target(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr in net for net in _ALLOWED_NETS)


def assert_lab_target(ip: str) -> str:
    """Return ip if it is inside the lab; otherwise raise OutOfScopeError.

    This is the hard stop that keeps the framework from ever scanning or
    attacking anything outside the two isolated lab subnets.
    """
    if not is_lab_target(ip):
        raise OutOfScopeError(
            f"REFUSED: {ip!r} is not inside the lab networks "
            f"({DMZ_NET}, {INTERNAL_NET}). This framework only operates in-lab."
        )
    return ip


def banner(title: str) -> str:
    line = "=" * 70
    return f"\n{line}\n  {title}\n  {datetime.now().isoformat(timespec='seconds')}\n{line}"


if __name__ == "__main__":
    # Self-test of the safety guard.
    print(banner("lab_config self-test"))
    for ip in ("172.16.10.5", "10.0.0.25", "8.8.8.8", "192.168.1.1"):
        try:
            assert_lab_target(ip)
            print(f"  [ALLOW] {ip}")
        except OutOfScopeError as e:
            print(f"  [BLOCK] {e}")
