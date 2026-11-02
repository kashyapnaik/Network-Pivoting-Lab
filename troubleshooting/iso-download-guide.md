# ISO Download & Verification Guide

**Verified:** 2026-11-01. Always re-check the live checksum file at download time — versions roll forward.

> **Save location suggestion:** `C:\Users\naikk\VirtualBox VMs\_ISOs\`
> (keep ISOs out of individual VM folders so they're easy to reuse and back up).

---

## 1. Kali Linux — the attacker (KALI-ATTACKER)

**Pick the FULL installer, NOT netinst.** Your lab VMs have no internet (isolated internal networks), and netinst downloads packages during install — it would fail. The full installer is self-contained and already includes nmap, metasploit, wireshark, proxychains4, netcat, python3, tcpdump, impacket, netexec, evil-winrm, and more.

| Field | Value |
|---|---|
| File | `kali-linux-2026.3-installer-amd64.iso` |
| Size | ~4.7 GiB |
| Download page | https://www.kali.org/get-kali/#kali-installer-images |
| Direct dir | https://cdimage.kali.org/current/ |
| SHA256 | `db9cbed33edb45727d16911813c2434fcd1419585007884153be22a03b30ec2f` |

On the Get Kali page choose **Installer** (the ~4.7 GB one), architecture **64-bit (amd64)**.

---

## 2. Ubuntu Server — the pivot (PIVOT01)

Use the **Live Server** ISO. It installs fully offline (just skip the "download updates" step during install). It's headless by design — exactly what we want for a low-RAM pivot.

| Field | Value |
|---|---|
| File | `ubuntu-24.04.5-live-server-amd64.iso` |
| Size | ~3.0 GB |
| Download page | https://ubuntu.com/download/server (→ "previous releases" for 24.04.5 LTS) |
| Direct dir | https://releases.ubuntu.com/24.04.5/ |
| SHA256 | `97f3d7ffb032c3eb3b23d2c8be9cc76e60c2c1f2c0146ba5ba9fe01cafae0fd8` |

---

## 3. Windows 11 Enterprise LTSC 2024 Evaluation — the target (WIN-TARGET01)

> **Note (why not Windows 10):** Windows 10 reached end-of-support in **October 2025**, and Microsoft has **retired the Windows 10 Enterprise evaluation** — its page now redirects to a "move to Windows 11" blog. So the target is **Windows 11 Enterprise LTSC 2024** instead. LTSC was chosen over standard 26H2 because it is lighter, has no consumer bloat, and lets you create a **local account** (no forced Microsoft sign-in). Everything the lab needs — SMB, WinRM, Defender, event logging — is present.

Free **90-day evaluation**, no product key needed. The Evaluation Center requires a short registration form (name / email / company / role) before the download links appear — **fill that yourself** (personal info).

| Field | Value |
|---|---|
| Edition | Windows 11 Enterprise **LTSC 2024**, **64-bit**, English (US) |
| File (as saved) | `windows11-enterprise-ltsc-2024-eval-x64.iso` |
| Build | 26100.1742 (CLIENT_LTSC_EVAL x64FRE en-us) |
| Size | 5,112,850,432 bytes (4.76 GB) — **verified complete by exact byte count** |
| Download page | https://www.microsoft.com/en-us/evalcenter/evaluate-windows-11-enterprise |
| SHA256 (recorded) | `67CEC5865EAA037A72DDC633A717A10A2BED50778862267223DDB9C60EF5DA68` |

> Microsoft does not publish an official SHA256 for eval ISOs, so the hash above is **our own record** (useful to detect later corruption), not an authenticity check. Integrity here is confirmed by the download matching the server's exact `Content-Length`.

### VM change this forced
Windows 11 has stricter requirements than Windows 10, so **WIN-TARGET01 was reconfigured**:
- Firmware switched **BIOS → EFI** (Win11 won't install on legacy BIOS)
- Added a virtual **TPM 2.0** chip
- Disk grown **50 GB → 65 GB** (Win11 minimum is 64 GB)
- OS type set to Windows 11 (64-bit); RAM 4 GB / 2 vCPU unchanged; still isolated on INTERNAL-NET

---

## 4. Verify every download (do this — it's an interview talking point)

On Windows, compute the SHA256 and compare it (case-insensitive) to the value above:

```powershell
Get-FileHash "C:\Users\naikk\VirtualBox VMs\_ISOs\kali-linux-2026.3-installer-amd64.iso" -Algorithm SHA256
```

```powershell
Get-FileHash "C:\Users\naikk\VirtualBox VMs\_ISOs\ubuntu-24.04.5-live-server-amd64.iso" -Algorithm SHA256
```

**Why it matters:** the hash proves the file wasn't corrupted in transit or tampered with on a mirror. If even one bit differs, the hash changes completely. This is integrity verification — a core security concept.

**Stronger (Kali only):** Kali signs its `SHA256SUMS` file with a GPG key. The gold-standard check is to verify that GPG signature (`SHA256SUMS.gpg`) against Kali's published key, which proves the *checksum list itself* is authentic — not just that your file matches a list a mirror handed you. I can walk you through that if you want.

---

## 5. Why not just one big download command?
The Kali and Ubuntu ISOs are direct links I can fetch for you (with your go-ahead). The Windows ISO sits behind a Microsoft form that needs your personal details, so that one is yours to download in a browser. Once the files exist, I'll attach each ISO to its VM's DVD drive and we start installs.
