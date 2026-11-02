# Phase 9 — Advanced Pivoting (SSH forwarding & multi-hop)

The Chisel reverse SOCKS tunnel (Phases 5–6) is one way to pivot. This reference
covers the **SSH-native** techniques every pentester must know, the multi-hop
case, and the precise differences between the concepts people conflate.

Lab addressing used in the examples:
```
KALI 172.16.10.5   PIVOT 172.16.10.15 / 10.0.0.15   WIN-TARGET 10.0.0.25
```

---

## The four concepts (get these straight)

| Concept | What it is | Granularity |
|---|---|---|
| **Port forwarding** | One fixed local port → one fixed remote `host:port` | single destination |
| **SOCKS proxying** | A proxy that forwards to **any** destination the pivot can reach | any destination, app must be SOCKS-aware (or use proxychains) |
| **IP routing** | Kernel forwards packets between interfaces (L3) | whole subnets, transparent, needs `ip_forward` + routes |
| **Tunneling** | Encapsulating traffic inside another protocol (SSH, WebSocket, DNS…) | the transport that carries any of the above across a boundary |
| **Network pivoting** | Using a compromised host's network position to reach otherwise-unreachable segments | the umbrella goal; achieved via the above |

Key distinction: **port forwarding** gives you one door; **SOCKS** gives you the
whole building (every host:port the pivot can reach) through one proxy port;
**IP routing** would route entire subnets but is noisy and was deliberately left
off in this lab (`net.ipv4.ip_forward = 0`).

---

## 1. SSH Local port forwarding (`-L`)

Bring a remote service to a local port on the attacker.

```bash
# On KALI: expose WIN-TARGET's SMB (10.0.0.25:445) as 127.0.0.1:4445 locally
ssh -L 127.0.0.1:4445:10.0.0.25:445 pivot@172.16.10.15
# then, in another shell:
nxc smb 127.0.0.1:4445 -u labadmin -p 'Lab@12345'
```
```
KALI:4445 ──SSH tunnel──▶ PIVOT ──▶ 10.0.0.25:445
```
Good for **one** known service. You pre-declare the destination.

## 2. SSH Dynamic port forwarding (`-D`) = SOCKS over SSH

The SSH-native equivalent of the Chisel SOCKS tunnel.

```bash
# On KALI: open a SOCKS proxy on 1081 that exits from the pivot
ssh -D 127.0.0.1:1081 pivot@172.16.10.15
# point proxychains at socks5 127.0.0.1 1081, then:
proxychains4 nxc smb 10.0.0.25 -u labadmin -p 'Lab@12345'
```
```
KALI:1081 (SOCKS) ──SSH──▶ PIVOT ──▶ anything on 10.0.0.0/24
```
Reach **any** internal host:port through one proxy — no need to know destinations
in advance. This is the preferred quick pivot when you have SSH to the pivot.

## 3. SSH Remote port forwarding (`-R`)

Push a service from the attacker's side **back** through the pivot, or (classic
use) get a callback when you only have an outbound path — the SSH analogue of
Chisel's *reverse* mode.

```bash
# From a compromised PIVOT that can reach KALI: expose pivot-side 10.0.0.25:445
# onto KALI's 127.0.0.1:4445
ssh -R 127.0.0.1:4445:10.0.0.25:445 attacker@172.16.10.5
```
Use when the victim can only make **outbound** connections (NAT/firewall) — the
tunnel is initiated from inside, just like the reverse Chisel client.

## 4. Multi-hop pivoting (pivot through a pivot)

When a **second** isolated network sits behind a second pivot:
```
KALI ── DMZ ── PIVOT1 ── INTERNAL ── PIVOT2 ── DEEP-NET ── DEEP-TARGET
```
Chain SOCKS proxies or use SSH `ProxyJump`:
```bash
# SSH straight to a 2nd-hop host, bouncing through pivot1 then pivot2:
ssh -J pivot@172.16.10.15,user@10.0.0.50 deepuser@10.1.0.10

# Or stack dynamic proxies: run chisel/ssh -D on pivot2 reachable *through*
# pivot1's proxy, then chain them in proxychains (proxy_dns off, strict_chain):
#   socks5 127.0.0.1 1080   # hop 1 (pivot1)
#   socks5 127.0.0.1 1081   # hop 2 (pivot2)
```
**Rule:** build multi-hop only **after** the basic two-network pivot works — add
one hop at a time and verify reachability at each layer (`internal_scan.py`).

---

## Chisel vs SSH forwarding — when to use which

| | Chisel (used in this lab) | SSH `-D`/`-L`/`-R` |
|---|---|---|
| Needs on victim | a dropped binary | an SSH account/session |
| Direction | easy **reverse** (victim calls out) | `-R` for reverse, `-D`/`-L` for forward |
| Stealth | hacktool (AV-flagged) | lives off the land (ssh is normal) |
| Best for | no SSH / need reverse from inside | you already have SSH to the pivot |

Both deliver the same outcome — a SOCKS proxy on the attacker that exits from the
pivot — which is exactly what `proxychains` then rides to attack the internal net.

---

## Why this lab left IP routing OFF

Enabling `net.ipv4.ip_forward=1` + routes on the pivot would let the attacker
route **entire subnets** transparently. It's powerful but: (a) noisy/obvious,
(b) a bigger blast radius, and (c) not representative of a stealthy foothold. The
brief explicitly said *"do not enable unrestricted IP forwarding."* Tunneling +
SOCKS achieves the goal with a far smaller footprint — the attacker only ever
touches the specific host:ports they choose.
