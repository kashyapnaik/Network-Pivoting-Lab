#!/usr/bin/env python3
"""
dmz_scan.py — Phase 4 recon. TCP-connect scan of hosts on the DMZ network
(172.16.10.0/24) from the attacker. Pure-stdlib (no nmap needed).

Usage:  python3 dmz_scan.py [--ports 22,80,445,3389,8080]
SAFETY: refuses any address outside the lab subnets via lab_config.assert_lab_target.
"""
import argparse
import socket
import sys
from concurrent.futures import ThreadPoolExecutor

from lab_config import (DMZ_NET, assert_lab_target, OutOfScopeError,
                        get_logger, banner)
import ipaddress

log = get_logger("dmz_scan")
DEFAULT_PORTS = [22, 80, 135, 139, 443, 445, 3389, 5985, 8080]


def tcp_open(ip, port, timeout=1.0):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        return False


def scan_host(ip, ports):
    try:
        assert_lab_target(ip)
    except OutOfScopeError as e:
        log.error(str(e))
        return ip, []
    open_ports = [p for p in ports if tcp_open(ip, p)]
    return ip, open_ports


def main():
    ap = argparse.ArgumentParser(description="DMZ TCP-connect scan (lab only).")
    ap.add_argument("--ports", default=",".join(map(str, DEFAULT_PORTS)))
    ap.add_argument("--net", default=DMZ_NET, help="lab subnet to sweep")
    args = ap.parse_args()
    ports = [int(p) for p in args.ports.split(",") if p.strip()]

    print(banner(f"DMZ SCAN {args.net}"))
    net = ipaddress.ip_network(args.net)
    hosts = [str(h) for h in net.hosts()]

    found = {}
    with ThreadPoolExecutor(max_workers=64) as ex:
        for ip, open_ports in ex.map(lambda h: scan_host(h, ports), hosts):
            if open_ports:
                found[ip] = open_ports
                log.info("UP  %-15s open: %s", ip, open_ports)

    if not found:
        log.info("No hosts with the scanned ports open were found on %s.", args.net)
    else:
        log.info("Scan complete: %d live host(s) with open ports.", len(found))
    return 0


if __name__ == "__main__":
    sys.exit(main())
