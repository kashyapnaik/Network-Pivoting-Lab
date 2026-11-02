#!/usr/bin/env python3
"""
log_analyzer.py — Phase 11 (blue team). Scan the framework's own logs and any
Chisel logs for indicators of pivoting/lateral movement, and print the Windows
Event IDs an analyst should correlate.

Usage:  python3 log_analyzer.py [--logdir ../logs] [extra_log_files...]
Read-only. Pattern-matches; does not modify anything.
"""
import argparse
import glob
import os
import re
import sys

from lab_config import LOG_DIR, get_logger, banner

log = get_logger("log_analyzer")

# (regex, human description) — indicators of the attack chain.
IOCS = [
    (r"Reverse tunnelling enabled|R:socks|proxy#R:127\.0\.0\.1:1080", "Chisel reverse SOCKS tunnel"),
    (r"Connected \(Latency", "Chisel client connected to attacker"),
    (r"Pwn3d!", "NetExec administrative compromise"),
    (r"Executed command", "Remote command execution"),
    (r"socks5 127\.0\.0\.1 1080", "proxychains pointed at tunnel"),
    (r"nxc |netexec |crackmapexec ", "credential/SMB tooling activity"),
]

WINDOWS_EVENT_IDS = {
    4624: "Successful logon (type 3 = network) — watch for 'labadmin'",
    4625: "Failed logon — credential testing",
    4648: "Logon with explicit credentials",
    4672: "Special privileges assigned (admin logon)",
    4688: "Process creation (enable command-line auditing)",
    5140: "Network share accessed",
    5145: "Network share object checked (detailed file access)",
    5156: "Windows Filtering Platform allowed a connection (445/5985)",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logdir", default=LOG_DIR)
    ap.add_argument("extra", nargs="*", help="extra log files (e.g. /tmp/chiselserver.log)")
    args = ap.parse_args()

    print(banner("LOG ANALYZER (blue-team view)"))
    files = glob.glob(os.path.join(args.logdir, "*.log")) + list(args.extra)
    files = [f for f in files if os.path.isfile(f)]
    if not files:
        log.warning("No log files found in %s", args.logdir)
    hits = 0
    for f in files:
        try:
            text = open(f, errors="replace").read()
        except Exception as e:
            log.warning("cannot read %s: %s", f, e)
            continue
        for rx, desc in IOCS:
            found = re.findall(rx, text)
            if found:
                hits += 1
                log.info("[IOC] %-40s x%-3d in %s", desc, len(found), os.path.basename(f))
    if hits == 0:
        log.info("No pivoting/lateral-movement IOCs found in local logs.")
    print(banner("WINDOWS EVENT IDs TO CORRELATE ON THE TARGET"))
    for eid, desc in WINDOWS_EVENT_IDS.items():
        log.info("  %-5d %s", eid, desc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
