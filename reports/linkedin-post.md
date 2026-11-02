# LinkedIn Post — Final Draft (project complete)

**How to post:** paste the text below. Attach the screenshots as a **carousel** in the
order listed — that order tells the whole story. Swap in your GitHub repo link.

**Carousel images (from `screenshots/`), in order:**
1. `02-kali-attacker-isolation-proof.png` — attacker can't reach the target ("Network is unreachable")
2. `03-pivot-bridge-reaches-both.png` — the pivot reaches both networks
3. `06-tunnel-reaches-internal-network.png` — the tunnel carries traffic into the internal net
4. `07-lateral-movement-pwned.png` — **(Pwn3d!)** admin on the Windows target
5. `09-remote-command-execution-rce.png` — running commands on the target through the tunnel
6. `10-packet-capture-tunnel-vs-internal.png` — the blue-team packet view

---

🛡️ I built a full **Network Pivoting & Lateral Movement lab** from scratch — and took it end to end: from an attacker with *no route* to a target, all the way to **admin + remote code execution**, then flipped to the **blue team** to detect and fix it.

Not a tutorial follow-along. Three VMs, two isolated networks, and every step proven with real output (screenshots 👇).

🧱 𝗧𝗵𝗲 𝘀𝗲𝘁𝘂𝗽 (VirtualBox, fully isolated):
• KALI-ATTACKER (172.16.10.5) — DMZ only
• PIVOT01 — dual-homed Ubuntu server bridging DMZ ↔ Internal
• WIN-TARGET01 (10.0.0.25) — Windows 11 LTSC, internal only

⚔️ 𝗧𝗵𝗲 𝗸𝗶𝗹𝗹 𝗰𝗵𝗮𝗶𝗻:
1️⃣ Proved segmentation — Kali literally gets "Network is unreachable" to the target
2️⃣ Dropped a **Chisel reverse SOCKS tunnel** through the pivot
3️⃣ Routed tools through it with **proxychains**
4️⃣ Enumerated the internal Windows host's SMB/WinRM
5️⃣ **Lateral movement** — a weak local-admin cred → NetExec `(Pwn3d!)`
6️⃣ **RCE** — ran PowerShell on the target, through the pivot

🔵 𝗧𝗵𝗲𝗻 𝘁𝗵𝗲 𝗱𝗲𝗳𝗲𝗻𝗱𝗲𝗿'𝘀 𝘀𝗶𝗱𝗲:
• A tcpdump on the pivot showing how the tunnel **hides** the attack from a DMZ sensor and **masks** the attacker's IP from an internal one
• Windows Event IDs mapped to each stage (4624 type 3, 4672, 5140…)
• A remediation plan where removing the dual-homing *or* default-deny egress breaks the whole chain

🧠 𝗪𝗵𝗮𝘁 𝗜 𝗮𝗰𝘁𝘂𝗮𝗹𝗹𝘆 𝗹𝗲𝗮𝗿𝗻𝗲𝗱 (the hard way):
• Why nmap "lies" through SOCKS but `nc` doesn't
• Why WMI/DCOM won't tunnel but WinRM will (single-port vs dynamic ports)
• TTL fingerprinting (64=Linux, 128=Windows), ICMP ≠ reachability
• Fighting UEFI/TPM, EFI graphics adapters, and eval-license shutdowns to get Win11 running
• Chisel gets flagged by Defender as a hacktool — which is itself a blue-team IOC

I also wrote it all up: a full pentest report, a 23-page build guide (every command + the *why*), and a 13-script Python automation framework with a safety guard that refuses any target outside the lab.

Honestly, the troubleshooting *was* the learning. Building and breaking (and fixing) your own lab teaches 10× more than any course.

🔗 Full repo + write-up: [your-github-link]

#CyberSecurity #PenetrationTesting #RedTeam #BlueTeam #NetworkSecurity #HomeLab #Kali #EthicalHacking #VAPT #Pivoting #LateralMovement #LearningInPublic

---

## Notes
- Everything above is **actually demonstrated** in the repo — no theoretical claims.
- Keep the carousel to 6 images; the order is the narrative (isolation → pivot → tunnel → Pwn3d! → RCE → blue team).
- If you want a shorter version for the body + "full story in comments," split at the 🔵 line.
