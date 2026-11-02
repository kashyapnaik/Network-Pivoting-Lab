#!/usr/bin/env python3
"""
initial_access_check.py — Phase 4. Confirm the pivot's SSH service (the
modeled initial-access foothold) is reachable on the DMZ and grab its banner.

This does NOT brute-force or exploit anything. It only checks reachability and
records the service banner, documenting the realistic foothold.

Usage:  python3 initial_access_check.py
"""
import socket
import sys

from lab_config import HOSTS, assert_lab_target, get_logger, banner

log = get_logger("initial_access_check")


def grab_banner(ip, port=22, timeout=5):
    assert_lab_target(ip)
    try:
        with socket.create_connection((ip, port), timeout=timeout) as s:
            s.settimeout(timeout)
            data = s.recv(256)
            return data.decode(errors="replace").strip()
    except Exception as e:
        return f"(no banner: {e})"


def main():
    print(banner("INITIAL ACCESS CHECK (pivot SSH)"))
    pivot = HOSTS["pivot_dmz"]
    log.info("Target foothold: %s:22 (PIVOT01, DMZ side)", pivot)
    b = grab_banner(pivot, 22)
    log.info("SSH banner: %s", b)
    if b.startswith("SSH-"):
        log.info("[OK] SSH is reachable on the pivot — this is the modeled foothold.")
        log.info("Note: use lab SSH credentials to log in; no exploitation performed here.")
        return 0
    log.error("SSH did not respond as expected on %s:22.", pivot)
    return 1


if __name__ == "__main__":
    sys.exit(main())
