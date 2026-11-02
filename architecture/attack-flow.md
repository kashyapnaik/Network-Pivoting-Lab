# Attack Flow — End to End

The full kill chain, as proven in this lab. Each step links to its evidence
screenshot in `screenshots/`.

```
                         ATTACKER controls PIVOT (foothold)
                                      │
 ┌──────────────┐   encrypted tunnel  │   ┌──────────────┐        ┌──────────────┐
 │ KALI-ATTACKER│◀════ Chisel 8080 ═══╪══▶│   PIVOT01    │───445─▶│ WIN-TARGET01 │
 │  172.16.10.5 │  (reverse SOCKS)    │   │ .15 / 10.0.0.15│──5985─▶│  10.0.0.25   │
 │  SOCKS :1080 │                     │   │ dual-homed    │        │  labadmin    │
 └──────┬───────┘                     │   └──────────────┘        └──────▲───────┘
        │ proxychains                 │                                  │
        └── nxc/evil-winrm ───────────┴──────────────────────────────────┘
                 (rides the tunnel into the internal network)
```

## Steps

| # | Step | Technique | Evidence |
|---|---|---|---|
| 0 | **Segmentation** — attacker can't reach target directly | (control being bypassed) | 01,02,03 |
| 1 | **Foothold** on the dual-homed pivot | SSH (lab creds) | — |
| 2 | **Reverse SOCKS tunnel** pivot → attacker | Chisel `R:socks` | 04,05 |
| 3 | **Reach internal net** through the tunnel | proxychains + SOCKS | 06 |
| 4 | **Expose + enumerate** target services | nxc SMB (445/5985 open) | 08 |
| 5 | **Lateral movement** — admin auth | nxc SMB `(Pwn3d!)` | 07 |
| 6 | **RCE** on the target | nxc WinRM `-X` | 09 |
| 7 | **(blue team)** packet view from the pivot | tcpdump | 10 |

## The single sentence

> A weak local-admin credential on an internal host, plus a dual-homed pivot the
> attacker could tunnel through, let an attacker with **no route** to the internal
> network gain **admin + RCE** on an internal Windows box — defeating network
> segmentation without ever touching it directly.

## Defender's counter (see `detection/` and `remediation/`)

- **Detect:** hacktool + new egress on the pivot; local-admin network logon (4624
  type 3) + admin-share access (5140) + WinRM shell on the target.
- **Prevent:** kill the dual-homing, default-deny egress, remove the weak admin,
  scope SMB/WinRM to jump hosts. Any one of the first two breaks the chain.
