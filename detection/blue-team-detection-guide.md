# Blue-Team Detection Guide — Pivoting & Lateral Movement

How a defender detects the exact attack this lab demonstrates. Organized by the
**three vantage points** a SOC has: the compromised pivot (egress), the network,
and the target host (authentication & execution).

> Mapped to the attack we actually ran: Chisel reverse SOCKS tunnel → proxychains
> → NetExec SMB auth (`Pwn3d!`) → WinRM RCE.

---

## Detection philosophy

An attacker pivoting through a compromised host leaves evidence in three places:

1. **On the pivot** — a new outbound connection "calling home," a proxy listener, and a hacktool on disk.
2. **On the wire** — a long-lived, low-volume encrypted session to an unusual destination, plus internal traffic that "appears" from the pivot.
3. **On the target** — network logons, privilege use, share access, and remote command execution.

No single signal is proof; **correlation** across these is what turns noise into a detection.

---

## 1. Pivot host (Linux) indicators

| Indicator | How to see it | Why it matters |
|---|---|---|
| Unexpected **outbound** connection | `ss -tnp` / `netstat -antp` — a `chisel` process with an established session to an odd host:port (here `172.16.10.5:8080`) | The reverse tunnel's "call home" |
| **SOCKS/proxy listener** | `ss -tlnp` shows a process listening that normally shouldn't | Local half of the tunnel |
| **Hacktool on disk** | file hash / AV; `chisel` is flagged as a PUA/HackTool by Microsoft Defender (confirmed in this lab) | Strong IOC |
| New long-running process | `ps aux`, auditd `execve` | Attacker tooling |
| Egress to a **non-business** port/host | firewall/netflow logs | Tunnels hide in 80/443/8080 |

**auditd rule idea** (process execution):
```
-a always,exit -F arch=b64 -S execve -F path=/usr/local/bin/chisel -k pivot_tool
-a always,exit -F arch=b64 -S execve -k exec_watch
```

**Quick triage one-liner:**
```bash
ss -tnp state established '( dport != :22 )' | grep -vE '127.0.0.1'
```

---

## 2. Network indicators

- A **single long-lived TCP/WebSocket** session from the pivot to the attacker, low bandwidth but persistent (the tunnel control channel).
- Internal SMB/WinRM sessions to the target that **originate from the pivot's internal IP** (`10.0.0.15`), not from a normal management host.
- **TTL/OS mismatch** and timing anomalies.
- If TLS-inspecting: a WebSocket upgrade (`Connection: Upgrade`) to a non-standard service.

A segment that should see **no** cross-boundary traffic suddenly carrying SMB/WinRM from the DMZ-facing host is the tell.

---

## 3. Windows target — the Security event log

This is the richest source. The lateral movement generated (or would generate, with auditing on):

| Event ID | Meaning | What our attack produced |
|---|---|---|
| **4624** | Successful logon. **Logon type 3 = network** | `labadmin` network logon from the pivot's IP |
| **4625** | Failed logon | any mistyped/sprayed creds during access |
| **4648** | Logon using explicit credentials | tooling passing creds |
| **4672** | Special privileges assigned to new logon | admin logon (because `labadmin` is a local admin) |
| **4688** | A new process was created (+command line, if enabled) | exec method spawning processes |
| **5140** | A network share was accessed | `C$` / `ADMIN$` access |
| **5145** | Network share object (file) checked | detailed share file access |
| **5156** | WFP permitted a connection | inbound to 445 / 5985 |

**Also valuable:**
- **WinRM Operational log**: `Microsoft-Windows-WinRM/Operational` — remote shell creation.
- **PowerShell logs**: Script Block Logging (4104) and Module Logging — the commands run via WinRM.
- **Microsoft Defender**: Operational log for detections (the attacker's tooling, if dropped on the host).

### The high-fidelity signal for *this* attack
A **4624 type 3** for a **local** account (`WIN-TARGET01\labadmin`, not a domain account) from an **internal server's IP**, immediately followed by **4672** (admin) and **5140** (`ADMIN$`/`C$`), then **WinRM** shell creation. That specific chain = remote admin lateral movement.

---

## What each attack stage looked like to the blue team

| Attack stage | Blue-team evidence |
|---|---|
| Chisel tunnel up | Pivot: outbound session + SOCKS listener; `chisel` binary (Defender PUA) |
| proxychains enum | Target: 5156 (allowed 445/5985); possibly 4625 if creds tested |
| `nxc smb … (Pwn3d!)` | Target: 4624 type 3 (labadmin) + 4672 + 5140 (`C$`,`ADMIN$`) |
| `nxc winrm -X` (RCE) | Target: WinRM Operational + 4688 + PowerShell 4104 |

---

## Detection rules (conceptual)

1. **Local-admin network logon from a server subnet**
   `EventID=4624 AND LogonType=3 AND TargetUserName is local AND SourceIP in server_subnet` → alert.
2. **Admin share access from non-admin host**
   `EventID=5140 AND ShareName in (ADMIN$, C$) AND SourceIP not in jump_hosts` → alert.
3. **Hacktool on a server** — AV/EDR detection of chisel/ligolo/socks on any host → high priority.
4. **New persistent outbound from a DMZ host** — netflow: long-lived session to a new external/unusual host → investigate.
5. **WinRM shell creation** outside change windows / from unexpected source → alert.

Centralize with **Windows Event Forwarding (WEF)** or a SIEM; the `log_analyzer.py`
script in `scripts/` demonstrates the IOC-matching idea on collected logs.

---

## Takeaway

The attack is quiet but not invisible. The combination of **(a)** a hacktool + new
egress on the pivot and **(b)** a local-admin network logon + admin-share access +
remote shell on the target is a reliable, high-confidence detection — *if* the
right auditing is enabled (see `windows-audit-policy-setup.md`).
