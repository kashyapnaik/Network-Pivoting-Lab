#!/usr/bin/env python3
"""
tunnel_verify.py — Phase 5 check. Confirm the reverse Chisel SOCKS5 proxy is
live on the attacker, then prove it reaches the INTERNAL network by opening a
connection *through* the proxy to a known internal service.

Usage:  python3 tunnel_verify.py
Verifies for real — it actually completes a SOCKS5 handshake and TCP connect;
it does not just claim success.
"""
import socket
import struct
import sys

from lab_config import (SOCKS_HOST, SOCKS_PORT, HOSTS, assert_lab_target,
                        get_logger, banner)

log = get_logger("tunnel_verify")


def socks5_connect(dst_ip, dst_port, timeout=8.0):
    """Open dst_ip:dst_port through the SOCKS5 proxy. Return True on success.

    Implements just enough of RFC1928 (no auth) to prove the tunnel carries
    traffic to the internal network.
    """
    assert_lab_target(dst_ip)
    s = socket.create_connection((SOCKS_HOST, SOCKS_PORT), timeout=timeout)
    try:
        s.sendall(b"\x05\x01\x00")                 # ver5, 1 method, no-auth
        if s.recv(2) != b"\x05\x00":
            raise RuntimeError("SOCKS5 no-auth not accepted")
        req = b"\x05\x01\x00\x01" + socket.inet_aton(dst_ip) + struct.pack(">H", dst_port)
        s.sendall(req)
        rep = s.recv(10)
        if len(rep) < 2 or rep[1] != 0x00:
            raise RuntimeError(f"SOCKS5 connect failed (reply code {rep[1] if len(rep) > 1 else '?'})")
        return True
    finally:
        s.close()


def proxy_listening():
    try:
        socket.create_connection((SOCKS_HOST, SOCKS_PORT), timeout=3).close()
        return True
    except Exception:
        return False


def main():
    print(banner("TUNNEL VERIFY (reverse SOCKS5)"))
    if not proxy_listening():
        log.error("SOCKS5 proxy NOT listening on %s:%s — is the Chisel tunnel up?",
                  SOCKS_HOST, SOCKS_PORT)
        log.error("Start it with: chisel_server.sh (Kali) + chisel_client.sh (pivot)")
        return 2
    log.info("SOCKS5 proxy is listening on %s:%s", SOCKS_HOST, SOCKS_PORT)

    # Prove the tunnel reaches the internal network: pivot's internal SSH, then Windows SMB.
    checks = [(HOSTS["pivot_internal"], 22, "pivot SSH (internal side)"),
              (HOSTS["windows"], 445, "Windows SMB")]
    ok = False
    for ip, port, label in checks:
        try:
            if socks5_connect(ip, port):
                log.info("THROUGH TUNNEL: reached %s:%s  (%s)  [OK]", ip, port, label)
                ok = True
        except Exception as e:
            log.warning("through tunnel: %s:%s (%s) -> %s", ip, port, label, e)
    if ok:
        log.info("TUNNEL VERIFIED: traffic is reaching the internal network via the pivot.")
        return 0
    log.error("Tunnel is up but no internal service responded (targets may be down/firewalled).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
