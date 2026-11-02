#!/usr/bin/env python3
"""
network_check.py — show this machine's interfaces/addresses/routes and say
which lab network(s) it is attached to. Intended to run on Kali or the pivot.

Usage:  python3 network_check.py
Read-only.
"""
import shutil
import subprocess
import sys

from lab_config import DMZ_NET, INTERNAL_NET, is_lab_target, get_logger, banner

log = get_logger("network_check")


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=15).stdout
    except Exception as e:
        log.warning("command failed %s: %s", cmd, e)
        return ""


def my_ipv4_addresses():
    """Return a list of this host's IPv4 addresses (Linux `ip -o -4 addr`)."""
    addrs = []
    out = run(["ip", "-o", "-4", "addr", "show"])
    for line in out.splitlines():
        parts = line.split()
        # format: "2: eth0 inet 172.16.10.5/24 ..."
        for i, tok in enumerate(parts):
            if tok == "inet" and i + 1 < len(parts):
                addrs.append(parts[i + 1].split("/")[0])
    return addrs


def main():
    print(banner("NETWORK CHECK"))
    if not shutil.which("ip"):
        log.error("`ip` not found — this script expects a Linux host (Kali/pivot).")
        return 1

    log.info("Interfaces / addresses:\n%s", run(["ip", "-br", "addr"]).strip())
    log.info("Routing table:\n%s", run(["ip", "route"]).strip())

    addrs = my_ipv4_addresses()
    log.info("Detected IPv4 addresses: %s", addrs or "(none)")
    for a in addrs:
        tag = "LAB" if is_lab_target(a) else "non-lab"
        log.info("  %s -> %s", a, tag)

    on_dmz = any(a.startswith("172.16.10.") for a in addrs)
    on_int = any(a.startswith("10.0.0.") for a in addrs)
    role = {
        (True, True): "DUAL-HOMED PIVOT (both DMZ and INTERNAL)",
        (True, False): "DMZ host (attacker side)",
        (False, True): "INTERNAL host (target side)",
    }.get((on_dmz, on_int), "not on a known lab network")
    log.info("This host looks like: %s", role)
    log.info("Lab nets: DMZ=%s INTERNAL=%s", DMZ_NET, INTERNAL_NET)
    return 0


if __name__ == "__main__":
    sys.exit(main())
