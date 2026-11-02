# Network Topology — Network Pivoting Lab

## Diagram

```
                       ┌───────────────────────────┐
                       │       KALI-ATTACKER        │
                       │   172.16.10.5  (planned)   │
                       │   NIC1 ── DMZ-NET           │
                       └──────────────┬──────────────┘
                                      │
            ===========  DMZ-NET (172.16.10.0/24)  ===========
                                      │
                       ┌──────────────┴──────────────┐
                       │          PIVOT01             │
                       │  NIC1 172.16.10.15 (DMZ)     │
                       │  NIC2 10.0.0.15   (INTERNAL) │   <-- the ONLY bridge
                       └──────────────┬──────────────┘
                                      │
          =========  INTERNAL-NET (10.0.0.0/24)  =========
                                      │
                       ┌──────────────┴──────────────┐
                       │        WIN-TARGET01          │
                       │   10.0.0.25  (planned)       │
                       │   NIC1 ── INTERNAL-NET        │
                       └───────────────────────────────┘

   Host Windows 11  ──X──  (no adapter on either lab network; fully isolated)
   Home Wi-Fi       ──X──  (intnet only; no bridge/NAT on any lab VM)
```

## What a VirtualBox "Internal Network" is
An **Internal Network** (`--nic intnet`) is a private virtual Layer-2 switch that exists only inside VirtualBox. Only VMs that attach to the **same named** internal network can exchange frames. It is **not** connected to the host OS, and **not** connected to the internet. That property is what gives us free, enforced isolation — no firewall rule required to keep the lab off your home network.

- `DMZ-NET` = the switch shared by KALI-ATTACKER and PIVOT01.
- `INTERNAL-NET` = the switch shared by PIVOT01 and WIN-TARGET01.

These networks are **defined by attachment**: they come into existence the moment a VM adapter references the name. There is no separate "create network" command, and no DHCP server is configured — every host gets a **static** IP set inside its own guest OS (done in a later phase), which is the deliberate, controlled approach.

## Planned IP addressing (set inside each guest, not at VBox level yet)
| VM | Interface | Network | IP | Role |
|---|---|---|---|---|
| KALI-ATTACKER | NIC1 | DMZ-NET | 172.16.10.5 | Attacker foothold |
| PIVOT01 | NIC1 | DMZ-NET | 172.16.10.15 | Pivot, DMZ side |
| PIVOT01 | NIC2 | INTERNAL-NET | 10.0.0.15 | Pivot, internal side |
| WIN-TARGET01 | NIC1 | INTERNAL-NET | 10.0.0.25 | Internal target |

## Expected connectivity (the isolation contract)
| From → To | Result | Why |
|---|---|---|
| Kali → PIVOT01 (172.16.10.15) | ✅ reachable | Same DMZ-NET switch |
| Kali → PIVOT01 (10.0.0.15) | ❌ unreachable | Kali has no interface/route on INTERNAL-NET |
| Kali → WIN-TARGET01 (10.0.0.25) | ❌ unreachable (directly) | No L2 path; must tunnel through PIVOT01 |
| PIVOT01 → Kali | ✅ reachable | Same DMZ-NET switch |
| PIVOT01 → WIN-TARGET01 | ✅ reachable | Same INTERNAL-NET switch |
| WIN-TARGET01 → Kali | ❌ unreachable | No interface/route toward DMZ-NET |
| Any lab VM → Internet / home Wi-Fi | ❌ unreachable | intnet has no NAT/bridge |

The entire point of the lab: Kali can only reach WIN-TARGET01 **after** establishing a tunnel/pivot through PIVOT01 (later phases). The topology itself guarantees there is no shortcut.

## VM shell specs as built (Phase 2/3)
| VM | OS type | vCPU | RAM | Disk (dynamic VDI) | Adapters |
|---|---|---|---|---|---|
| KALI-ATTACKER | Debian_64 | 2 | 3072 MB | 40 GB | NIC1 intnet DMZ-NET |
| PIVOT01 | Ubuntu_64 | 1 | 1536 MB | 20 GB | NIC1 DMZ-NET, NIC2 INTERNAL-NET |
| WIN-TARGET01 | Windows10_64 | 2 | 4096 MB | 50 GB | NIC1 intnet INTERNAL-NET |

Clipboard and drag-and-drop are **disabled** on all three (host↔guest isolation hygiene). Promiscuous mode is **denied** on every adapter.

## Not done yet (next phases)
- No OS is installed — these are empty shells booting to an empty DVD.
- Static IPs are not yet set (done inside each guest after install).
- No tools, no services, no firewall rules yet.
