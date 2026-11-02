# Phase 1 — Host System Inspection & Feasibility Report

**Date:** 2026-11-01
**Host OS:** Windows 11 Home Single Language (build 26300)
**Purpose:** Determine whether this laptop can run the 3-VM Network Pivoting Lab, and recommend resource allocation.

---

## 1. Raw inspection results

| Resource | Finding | Verdict |
|---|---|---|
| **CPU** | 12th Gen Intel Core i3-1215U — 6 physical cores (2 Performance + 4 Efficiency), 8 logical threads | OK (entry-level, but enough) |
| **RAM** | 15.71 GB total; **only 3.64 GB free at scan time** | Tight — host is heavily loaded right now |
| **Disk** | C: 476 GB total, **243 GB free** | Plenty |
| **VirtualBox** | Installed at default path, **version 7.2.18 r175117** | Modern, good |
| **Virtualization (VT-x)** | **Enabled in firmware** (a hypervisor is already running, which proves VT-x is on) | OK — but see the big caveat below |
| **Existing VMs** | `"linux "` and `Voidrix` | **Will NOT be modified or deleted** |
| **Existing internal net** | `Kashyap'sFirewalLAN` | **Will NOT be touched; new nets get distinct names** |
| **Host-only net** | `192.168.56.1/24` (default) | Not used by this lab |

### Why the VT-x flags looked contradictory
The first scan showed `VirtualizationFirmwareEnabled: False`, but the reliable check showed `HyperVisorPresent: True`. These are not in conflict. A Windows hypervisor is **already running and has claimed the VT-x extensions**, so the host OS can no longer "see" them directly — hence the `False`. The presence of a running hypervisor is itself proof that hardware virtualization is enabled in your BIOS/UEFI.

---

## 2. The one caveat that matters: VBS / Memory Integrity is ON

Your scan showed:
- **Memory Integrity (HVCI) = Enabled (`1`)**
- **Virtualization-Based Security (VBS) = Running (`2`)**

**What this means:** Windows is running its own hypervisor (for VBS/Memory Integrity). VirtualBox 7.x still works in this state, but it is forced to run **on top of** the Windows Hypervisor Platform instead of talking to the CPU directly. This adds a measurable performance penalty to VMs — most noticeable with 3 VMs running at once on a low-power U-series i3.

**You have two choices:**

| Option | Performance | Trade-off |
|---|---|---|
| **A. Leave VBS on (recommended first)** | Slower, but works | Keeps your host security feature intact. Try the lab this way first. |
| **B. Disable Memory Integrity** | Faster VMs | Reduces a host security feature. This is a **host OS security setting** — I will **not** change it for you. If you want it, you'd do it yourself via Settings → Privacy & security → Windows Security → Device security → Core isolation → Memory integrity (off) → reboot. |

My recommendation: **start with Option A.** Only consider B if the VMs are unusably slow, and only because this is your personal lab machine.

---

## 3. Feasibility verdict: **YES, with a tight RAM budget**

The i3-1215U + 16 GB can run all three VMs **simultaneously** for a learning lab, provided you:
1. **Close other apps before labbing** (your free RAM was only 3.64 GB at scan time — most of your 16 GB was already in use by other programs).
2. Run the **Ubuntu pivot headless** (no desktop) to save RAM and CPU.
3. Accept that this is a *functional* lab, not a *fast* one. Scans and tunnels will work; they just won't be instant.

The CPU is the weakest link (2 real performance cores), but pivoting labs are I/O- and network-bound, not CPU-heavy, so it's fine.

---

## 4. Recommended resource allocation

### Profile A — "Comfortable" (use when you can free up RAM)
| VM | OS | vCPU | RAM | Disk | Notes |
|---|---|---|---|---|---|
| KALI-ATTACKER | Kali Linux | 2 | 3072 MB | 40 GB | GUI acceptable but XFCE, not GNOME |
| PIVOT01 | Ubuntu Server (headless) | 1 | 1536 MB | 20 GB | No desktop — SSH only |
| WIN-TARGET01 | Windows 10 Enterprise Eval | 2 | 4096 MB | 50 GB | Win10 eval is lighter than Win11 |
| **Host reserve** | — | — | **~7 GB** | — | For Windows 11 + browser |

**VM total: ~8.6 GB RAM.** Leaves ~7 GB for the host — safe if you close heavy apps.

### Profile B — "Survival" (if RAM is scarce)
Run only **two VMs at a time** (Kali + Pivot, OR Pivot + Windows): Kali 2560 MB, Pivot 1024 MB, Windows 3072 MB. You rarely need all three fully active at once during most phases.

### Why Windows 10 Eval over Windows 11
Windows 11 requires virtual TPM 2.0 + Secure Boot (VirtualBox 7.x supports this, but it's extra setup and heavier). The **Windows 10 Enterprise Evaluation** ISO is lighter, needs no TPM, installs faster, and is fully adequate for SMB/WinRM/Defender/Event-Log work. I recommend it unless you specifically need Win11.

---

## 5. Hard safety rules locked in for this build
- Your existing VMs `"linux "` and `Voidrix` — **never touched.**
- Your existing internal net `Kashyap'sFirewalLAN` — **never touched.** New nets will be named `DMZ-NET` and `INTERNAL-NET`.
- **No bridged/NAT adapters on the vulnerable VMs** — the lab uses VirtualBox *Internal Networks* only, so nothing is exposed to your home Wi-Fi.
- **No host partition changes, no host security-setting changes** without you doing them yourself.
- Snapshots taken before each major change.

---

## 6. Next step (Phase 2/3 preview — not yet executed)
Phase 2 (architecture) and Phase 3 (virtual networks) come next. The first *actionable* build step is creating the two isolated internal networks and the empty VM shells. That step changes nothing destructive and is fully reversible. I'll show you each `VBoxManage` command with an explanation before running it.
