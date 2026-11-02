#!/usr/bin/env python3
"""
host_check.py — Phase 1 helper. Report the host's CPU / RAM / disk and,
if VBoxManage is present, the lab VMs and their power state.

Usage:  python3 host_check.py
Runs read-only. Safe on any OS (degrades gracefully if a check is unavailable).
"""
import os
import shutil
import subprocess
import sys

from lab_config import get_logger, banner

log = get_logger("host_check")


def cpu_count():
    try:
        return os.cpu_count()
    except Exception:
        return "unknown"


def mem_gb():
    # Portable-ish: try psutil, fall back to /proc/meminfo, else unknown.
    try:
        import psutil
        return round(psutil.virtual_memory().total / 1024**3, 2)
    except Exception:
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal"):
                        return round(int(line.split()[1]) / 1024**2, 2)
        except Exception:
            return "unknown"


def disk_free_gb(path="/"):
    try:
        return round(shutil.disk_usage(path).free / 1024**3, 2)
    except Exception:
        return "unknown"


def vbox_vms():
    exe = shutil.which("VBoxManage") or shutil.which("VBoxManage.exe")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "list", "vms"], capture_output=True,
                             text=True, timeout=15)
        running = subprocess.run([exe, "list", "runningvms"], capture_output=True,
                                 text=True, timeout=15)
        return out.stdout.strip(), running.stdout.strip()
    except Exception as e:
        log.warning("VBoxManage query failed: %s", e)
        return None


def main():
    print(banner("HOST CHECK (Phase 1)"))
    log.info("CPU logical cores : %s", cpu_count())
    log.info("Total RAM (GB)    : %s", mem_gb())
    log.info("Free disk (GB)    : %s", disk_free_gb())

    vms = vbox_vms()
    if vms is None:
        log.info("VBoxManage not found on this host (skipping VM inventory).")
    else:
        registered, running = vms
        log.info("Registered VMs:\n%s", registered or "  (none)")
        log.info("Running VMs:\n%s", running or "  (none)")
    log.info("host_check complete.")


if __name__ == "__main__":
    sys.exit(main())
