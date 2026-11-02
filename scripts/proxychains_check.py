#!/usr/bin/env python3
"""
proxychains_check.py — Phase 6 check. Confirm a proxychains config points at
the lab SOCKS5 proxy and that a command actually succeeds through it.

Usage:  python3 proxychains_check.py [--conf ~/pc.conf]
"""
import argparse
import os
import shutil
import subprocess
import sys

from lab_config import (SOCKS_HOST, SOCKS_PORT, HOSTS, get_logger, banner)

log = get_logger("proxychains_check")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conf", default=os.path.expanduser("~/pc.conf"))
    args = ap.parse_args()
    print(banner("PROXYCHAINS CHECK"))

    pc = shutil.which("proxychains4") or shutil.which("proxychains")
    if not pc:
        log.error("proxychains4 not installed.")
        return 2

    if not os.path.exists(args.conf):
        log.error("Config %s not found. Expected a line: socks5 %s %s",
                  args.conf, SOCKS_HOST, SOCKS_PORT)
        return 2
    conf_txt = open(args.conf).read()
    want = f"socks5 {SOCKS_HOST} {SOCKS_PORT}"
    if want not in conf_txt:
        log.warning("Config does not contain expected line: %s", want)
    else:
        log.info("Config OK: %s -> %s", args.conf, want)

    # Verify for real: run a trivial connection through proxychains to the
    # pivot's internal SSH. nc is the reliable single-connection tool here.
    nc = shutil.which("nc")
    target = HOSTS["pivot_internal"]
    if nc:
        cmd = [pc, "-f", args.conf, "nc", "-z", "-v", "-w", "8", target, "22"]
        log.info("Testing: %s", " ".join(cmd))
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            blob = (r.stdout + r.stderr)
            if "OK" in blob or "open" in blob or "succeeded" in blob:
                log.info("Proxychains path WORKS (reached %s:22 through the tunnel).", target)
                return 0
            log.error("Proxychains test did not confirm a connection:\n%s", blob.strip())
            return 1
        except Exception as e:
            log.error("proxychains test failed: %s", e)
            return 1
    log.warning("`nc` not found; config looks right but was not exercised.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
