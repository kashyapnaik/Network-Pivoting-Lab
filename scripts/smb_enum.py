#!/usr/bin/env python3
"""
smb_enum.py — Phase 7. Enumerate the internal target's SMB through the tunnel
using NetExec (nxc) via proxychains. Unauthenticated by default; pass --auth to
use the lab credentials.

Usage:
  python3 smb_enum.py                 # unauthenticated fingerprint
  python3 smb_enum.py --auth --shares # lab creds + list shares
SAFETY: target is lab-validated; credentials come only from lab_config.
"""
import argparse
import shutil
import subprocess
import sys
import os

from lab_config import (HOSTS, LAB_CREDS, assert_lab_target, get_logger, banner)

log = get_logger("smb_enum")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ip", nargs="?", default=HOSTS["windows"])
    ap.add_argument("--conf", default=os.path.expanduser("~/pc.conf"))
    ap.add_argument("--auth", action="store_true", help="use lab credentials")
    ap.add_argument("--shares", action="store_true", help="enumerate shares")
    args = ap.parse_args()
    assert_lab_target(args.ip)

    print(banner(f"SMB ENUM (through tunnel) {args.ip}"))
    pc = shutil.which("proxychains4") or shutil.which("proxychains")
    nxc = shutil.which("nxc") or shutil.which("netexec") or shutil.which("crackmapexec")
    if not (pc and nxc):
        log.error("Need proxychains and nxc/netexec installed.")
        return 2

    cmd = [pc, "-f", args.conf, nxc, "smb", args.ip]
    if args.auth:
        cmd += ["-u", LAB_CREDS["username"], "-p", LAB_CREDS["password"]]
    if args.shares:
        cmd += ["--shares"]
    log.info("Running: %s", " ".join(cmd[:4]) + " ... (creds hidden)")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        log.info("nxc output:\n%s", out)
        if "Pwn3d!" in out:
            log.info("[RESULT] Administrative access confirmed (Pwn3d!).")
        elif "[+]" in out:
            log.info("[RESULT] Valid credentials / connection confirmed.")
        else:
            log.info("[RESULT] No authenticated success (expected if unauthenticated).")
        return 0
    except subprocess.TimeoutExpired:
        log.error("nxc timed out through the tunnel (target down or tunnel slow).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
