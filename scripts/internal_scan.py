#!/usr/bin/env python3
"""
internal_scan.py — Phase 7. TCP-connect scan of the INTERNAL target *through
the tunnel*, using the SOCKS5 proxy directly (reliable — unlike nmap-over-SOCKS,
which mis-reports ports as 'filtered').

Usage:  python3 internal_scan.py [ip] [--ports 135,139,445,3389,5985]
Default target is the Windows host. SAFETY: lab-only via assert_lab_target.
"""
import argparse
import sys

from lab_config import HOSTS, assert_lab_target, OutOfScopeError, get_logger, banner
from tunnel_verify import socks5_connect, proxy_listening

log = get_logger("internal_scan")
DEFAULT_PORTS = [135, 139, 445, 3389, 5985, 5986, 22, 80, 443]
SERVICE = {135: "msrpc", 139: "netbios", 445: "smb", 3389: "rdp",
           5985: "winrm", 5986: "winrm-https", 22: "ssh", 80: "http", 443: "https"}


def main():
    ap = argparse.ArgumentParser(description="Scan internal host through the tunnel.")
    ap.add_argument("ip", nargs="?", default=HOSTS["windows"])
    ap.add_argument("--ports", default=",".join(map(str, DEFAULT_PORTS)))
    args = ap.parse_args()

    print(banner(f"INTERNAL SCAN (through tunnel) {args.ip}"))
    try:
        assert_lab_target(args.ip)
    except OutOfScopeError as e:
        log.error(str(e))
        return 2
    if not proxy_listening():
        log.error("SOCKS proxy not up — run tunnel_verify.py first.")
        return 2

    ports = [int(p) for p in args.ports.split(",") if p.strip()]
    found = []
    for p in ports:
        try:
            if socks5_connect(args.ip, p):
                found.append(p)
                log.info("OPEN  %-5d %s", p, SERVICE.get(p, "?"))
        except Exception:
            pass  # closed/filtered — stay quiet, only report open
    if found:
        log.info("Open ports on %s (via tunnel): %s", args.ip, found)
    else:
        log.info("No open ports found on %s via the tunnel (host down or firewalled).", args.ip)
    return 0


if __name__ == "__main__":
    sys.exit(main())
