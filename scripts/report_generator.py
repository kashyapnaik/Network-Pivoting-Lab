#!/usr/bin/env python3
"""
report_generator.py — Phase 14. Run the verification checks and emit a fresh
Markdown + JSON status report of the lab's current state (what is actually
reachable / proven right now), written to reports/.

Usage:  python3 report_generator.py
It VERIFIES live state (does not hard-code success): it checks the SOCKS proxy
and internal reachability through the tunnel before reporting them as working.
"""
import json
import os
import sys
from datetime import datetime

from lab_config import HOSTS, get_logger, banner
from tunnel_verify import proxy_listening, socks5_connect

log = get_logger("report_generator")
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports")


def live_checks():
    result = {"socks_proxy_listening": proxy_listening()}
    checks = {
        "pivot_internal_ssh_via_tunnel": (HOSTS["pivot_internal"], 22),
        "windows_smb_via_tunnel": (HOSTS["windows"], 445),
        "windows_winrm_via_tunnel": (HOSTS["windows"], 5985),
    }
    for name, (ip, port) in checks.items():
        ok = False
        if result["socks_proxy_listening"]:
            try:
                ok = socks5_connect(ip, port)
            except Exception:
                ok = False
        result[name] = ok
    return result


def main():
    print(banner("REPORT GENERATOR (live state)"))
    os.makedirs(REPORT_DIR, exist_ok=True)
    checks = live_checks()
    for k, v in checks.items():
        log.info("  %-35s %s", k, "OK" if v else "no")

    report = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "hosts": HOSTS,
        "live_checks": checks,
    }
    jpath = os.path.join(REPORT_DIR, "lab_status.json")
    with open(jpath, "w") as f:
        json.dump(report, f, indent=2)

    mpath = os.path.join(REPORT_DIR, "lab_status.md")
    with open(mpath, "w") as f:
        f.write(f"# Lab status — {report['generated']}\n\n")
        f.write("| Check | Result |\n|---|---|\n")
        for k, v in checks.items():
            f.write(f"| {k} | {'✅' if v else '❌'} |\n")
    log.info("Wrote %s and %s", jpath, mpath)
    return 0


if __name__ == "__main__":
    sys.exit(main())
