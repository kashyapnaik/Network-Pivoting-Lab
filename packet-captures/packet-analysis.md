# Phase 10 — Packet Analysis

A live capture taken **on the pivot** (`tcpdump -i any`) while the attack ran
through the tunnel. The pivot is the one place that sees *both* sides, which is
exactly what makes the analysis instructive.

- **Capture file:** `/tmp/pivot-capture.pcap` on PIVOT01 (~358 KB)
- **Filter:** `tcp port 8080 or tcp port 445 or tcp port 5985`
- **Evidence:** `capture-summary.png`, `capture-both-sides.png`

## Packet counts

| Traffic | Port | Interface | Packets |
|---|---|---|---|
| Chisel tunnel (to attacker) | 8080 | enp0s3 (DMZ) | **387** |
| SMB (to target) | 445 | enp0s8 (INTERNAL) | **214** |
| WinRM (to target) | 5985 | enp0s8 (INTERNAL) | **57** |

## The key finding — tunneling blinds each vantage point

**DMZ side (enp0s3):**
```
172.16.10.5.8080  > 172.16.10.15.49160 : Flags [.], ack ...
172.16.10.15.49160 > 172.16.10.5.8080  : Flags [.], ack ...
```
Every DMZ packet is the pivot ⇄ attacker Chisel WebSocket on 8080. A sensor on
DMZ-NET sees **only an encrypted tunnel to one host** — none of the SMB/WinRM
attack is visible here; it is encapsulated inside the tunnel.

**Internal side (enp0s8):**
```
10.0.0.15.39666 > 10.0.0.25.445 : Flags [S]  ...   (SYN)
10.0.0.25.445   > 10.0.0.15.39666: Flags [S.] ...  (SYN-ACK)
10.0.0.15.39666 > 10.0.0.25.445 : Flags [P.] len 51 (SMB data)
```
The SMB session appears to originate from the **pivot (10.0.0.15)** — the real
attacker's address (172.16.10.5) never appears on the internal network. The pivot
has effectively laundered the source.

## Why this matters (defensive takeaway)

- A **DMZ IDS** can't inspect the attack — it's inside the encrypted tunnel. The
  detectable signal there is *behavioural*: a long-lived outbound session to an
  unusual host:port (see `detection/blue-team-detection-guide.md`).
- An **internal IDS** sees the SMB/WinRM clearly, but attributes it to the pivot,
  not the attacker. Correlating "internal SMB from a DMZ-facing host" is the tell.
- This is precisely why **egress monitoring on the pivot** and **segmentation**
  (so a DMZ host can't reach internal SMB at all) are the highest-value controls.

## Reproduce

```bash
# on PIVOT01
sudo tcpdump -i any -w /tmp/pivot-capture.pcap 'tcp port 8080 or tcp port 445 or tcp port 5985'
# (in parallel) on KALI, through the tunnel:
proxychains4 -f ~/pc.conf nxc smb 10.0.0.25 -u labadmin -p 'Lab@12345' --shares
# stop tcpdump, then analyse:
sudo tcpdump -r /tmp/pivot-capture.pcap -nn 'tcp port 8080' | head   # DMZ: tunnel only
sudo tcpdump -r /tmp/pivot-capture.pcap -nn 'tcp port 445'  | head   # internal: SMB
```
Open the `.pcap` in Wireshark for full stream reassembly (Follow TCP Stream on
the 8080 flow shows the opaque tunnel; on the 445 flow shows the SMB negotiation).
