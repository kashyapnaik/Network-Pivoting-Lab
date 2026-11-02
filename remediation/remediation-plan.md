# Remediation Plan — Breaking the Pivot Chain

Each finding from the engagement, the control that fixes it, the **before → after**
state, and **how to prove the attack path is now blocked** (re-test). Controls are
ordered by impact: the first two alone break the demonstrated chain.

> The attack chain was: foothold on dual-homed pivot → reverse SOCKS tunnel →
> reach internal net → weak local-admin on target → admin + RCE. Remove any one
> critical link and the chain fails.

---

## F1 — Dual-homed host bridges isolated segments (High)

**Fix:** A DMZ host must **not** have an interface in the internal network. Remove the
second NIC. If a service genuinely must cross the boundary, place a **firewall**
between the segments that allows only the specific host:port:protocol needed —
never a general-purpose server with a foot in both.

| | State |
|---|---|
| **Before** | PIVOT01: `172.16.10.15` (DMZ) **and** `10.0.0.15` (internal) |
| **After** | PIVOT01 keeps only its DMZ interface; internal access is via a firewall rule, default-deny |

**Re-test / proof blocked:** From the compromised pivot, `ping`/`nc` to `10.0.0.25`
now **fails** (no route / firewall deny). The SOCKS tunnel still comes up, but it
can no longer reach the internal network — `tunnel_verify.py` reports the proxy up
but **no internal service reachable**.

---

## F2 — Weak local-administrator credential (Critical)

**Fix:** Eliminate weak, reused, and unnecessary local admins.
- Deploy **LAPS** (randomized, rotated local-admin passwords, unique per host).
- Enforce long passphrases + lockout policy.
- Remove `labadmin`-style standing local admins; use just-in-time elevation.

| | State |
|---|---|
| **Before** | `labadmin : Lab@12345`, local Administrators member, usable remotely |
| **After** | No weak local admin; remaining admin passwords are LAPS-managed and unique |

**Re-test / proof blocked:** `nxc smb 10.0.0.25 -u labadmin -p 'Lab@12345'` now
returns **authentication failure** (no `Pwn3d!`). Even if an attacker reaches 445,
there is no weak credential to abuse.

---

## F3 — Management services exposed to an untrusted segment (High)

**Fix:** Host firewall should allow **SMB (445)** and **WinRM (5985)** only from
designated management hosts / jump boxes, not from the whole subnet (and never
from a DMZ-facing host).

| | State |
|---|---|
| **Before** | 445 and 5985 reachable from the pivoted attacker |
| **After** | Inbound 445/5985 scoped to a jump-host IP via Windows Firewall rules |

**Windows Firewall scoping example:**
```powershell
# Restrict the WinRM/SMB inbound rules to a single management host
Set-NetFirewallRule -DisplayGroup "Windows Remote Management" -RemoteAddress 10.0.0.250
Set-NetFirewallRule -DisplayGroup "File and Printer Sharing" -RemoteAddress 10.0.0.250
```

**Re-test / proof blocked:** `internal_scan.py` through the tunnel now shows
**445/5985 closed/filtered** from the pivot's IP; only the jump host can connect.

---

## Supporting controls

### Egress filtering on the pivot (breaks the tunnel's "call home")
The reverse tunnel depends on the pivot making an **outbound** connection to the
attacker. Default-deny egress + alert on unexpected outbound sessions stops or
exposes it.
```bash
# Example (iptables): allow only required egress, drop the rest, log drops
iptables -P OUTPUT DROP
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT   # + your real business ports
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -j LOG --log-prefix "EGRESS-DROP "
```
**Proof blocked:** `chisel client …` can no longer establish the session; the
tunnel never forms.

### SSH hardening on the pivot (shrinks the initial foothold)
Key-only auth, no password login, no root login, fail2ban:
```
# /etc/ssh/sshd_config
PasswordAuthentication no
PermitRootLogin no
```

### Defender / EDR
Keep real-time protection on — it flagged the `chisel` hacktool in this lab.
Alert on PUA/hacktool detections anywhere in the estate.

### Network segmentation of the segmentation
Micro-segment internal hosts so one foothold cannot reach the whole `10.0.0.0/24`.
Host-based firewalls + VLAN ACLs limit east-west movement.

---

## Validation matrix (re-run after hardening)

| Control applied | Expected re-test result |
|---|---|
| Remove dual-homing (F1) | Pivot cannot reach `10.0.0.0/24`; tunnel reaches nothing internal |
| Remove weak admin (F2) | `nxc` auth fails — no `Pwn3d!` |
| Scope host firewall (F3) | 445/5985 filtered from pivot's IP |
| Egress default-deny | Chisel client cannot connect out |

Applying **F1 or the egress rule alone** already breaks the demonstrated chain;
applying all of them provides defense in depth.

> *Status:* controls documented and validated **by design**. Live re-test on the
> lab VMs (applying each control and re-running the attack) is the final step and
> is pending due to Windows-VM instability on the current host.
