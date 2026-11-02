# Automation Framework (`scripts/`)

A Python + shell framework that manages, verifies, and reports on the lab —
one script per phase. **Run the Python scripts on Kali** (the attacker), where
`proxychains4`, `nxc`, and the tunnel live. The shell scripts run where noted.

> **Safety is built in.** Every script imports `lab_config.py`, whose
> `assert_lab_target()` **refuses any IP outside the two lab subnets**
> (`172.16.10.0/24`, `10.0.0.0/24`). The scripts also *verify* their results —
> they check real connections and parse real tool output rather than claiming
> success blindly.

## Files

| Script | Phase | What it does | Runs on |
|---|---|---|---|
| `lab_config.py` | — | Shared constants, logging, **safety guard**. `python3 lab_config.py` self-tests the guard. | any |
| `host_check.py` | 1 | CPU/RAM/disk + VirtualBox VM inventory | host or Kali |
| `network_check.py` | 3 | Interfaces, routes, which lab net you're on | Kali / pivot |
| `dmz_scan.py` | 4 | TCP-connect sweep of the DMZ (stdlib, no nmap) | Kali |
| `initial_access_check.py` | 4 | Confirm pivot SSH foothold + banner (no exploit) | Kali |
| `chisel_server.sh` | 5 | Start the reverse-tunnel server | Kali |
| `chisel_client.sh` | 5 | Start the reverse SOCKS client | **pivot** |
| `tunnel_verify.py` | 5 | Prove SOCKS5 is up **and** reaches the internal net | Kali |
| `proxychains_check.py` | 6 | Validate proxychains config + a live test connection | Kali |
| `internal_scan.py` | 7 | Scan the internal target **through the tunnel** (SOCKS) | Kali |
| `smb_enum.py` | 7 | SMB fingerprint / share enum via `nxc` + proxychains | Kali |
| `lateral_movement_lab.py` | 8 | **Non-destructive** auth + read-only RCE with lab creds | Kali |
| `log_analyzer.py` | 11 | Hunt IOCs in logs; list Windows Event IDs to correlate | Kali |
| `report_generator.py` | 14 | Live-verify state, emit `reports/lab_status.{md,json}` | Kali |

## Typical run order (on Kali)

```bash
python3 lab_config.py            # confirm the safety guard works
python3 network_check.py         # where am I?
python3 initial_access_check.py  # pivot SSH foothold reachable?
./chisel_server.sh &             # start tunnel server (pivot runs chisel_client.sh)
python3 tunnel_verify.py         # is the tunnel carrying traffic to the internal net?
python3 proxychains_check.py     # proxychains wired to the SOCKS proxy?
python3 internal_scan.py         # what's open on 10.0.0.25 through the tunnel?
python3 smb_enum.py --auth --shares
python3 lateral_movement_lab.py  # the full, non-destructive demo
python3 log_analyzer.py /tmp/chiselserver.log   # blue-team view
python3 report_generator.py      # write a fresh status report
```

## Notes
- Credentials come **only** from `lab_config.py` (`LAB_CREDS`) and are throwaway lab values.
- `lateral_movement_lab.py` is deliberately read-only: no payloads, persistence, dumping, or writes on the target.
- Logs are written to `../logs/`. `__pycache__/` and `logs/` are git-ignored.
