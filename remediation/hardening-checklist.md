# Hardening Checklist

Actionable, prioritized. ⬛ = breaks the demonstrated chain on its own.

## Network / segmentation
- ⬛ Remove internal-side NIC from any DMZ host (no dual-homing).
- ⬛ Default-deny **egress** from DMZ/server hosts; allow only known business destinations; log drops.
- [ ] Put a firewall between DMZ and internal; allow only specific host:port flows.
- [ ] Micro-segment internal hosts (host firewalls + VLAN ACLs) to limit east-west movement.
- [ ] Alert on new long-lived outbound sessions from servers.

## Credentials / identity
- ⬛ Remove weak/standing local admins (no `labadmin`-style accounts).
- [ ] Deploy **LAPS** — unique, rotated local-admin passwords per host.
- [ ] Enforce long passphrases, lockout, and MFA where possible.
- [ ] Use just-in-time / tiered admin; no admin creds reused across tiers.

## Host hardening (Windows target)
- [ ] Scope SMB (445) & WinRM (5985) inbound to jump hosts only (`Set-NetFirewallRule -RemoteAddress`).
- [ ] Disable WinRM where unused; require HTTPS (5986) + restricted hosts where used.
- [ ] Disable SMBv1 (already off here) and require SMB signing (already on).
- [ ] Keep Defender/EDR real-time protection on; alert on PUA/hacktool detections.

## Host hardening (pivot / Linux)
- [ ] SSH key-only (`PasswordAuthentication no`, `PermitRootLogin no`), fail2ban.
- [ ] auditd rules for `execve` and known tool paths.
- [ ] Remove unnecessary listening services; `ss -tlnp` baseline.

## Detection (make the attack visible)
- [ ] Enable audit subcategories: Logon, Special Logon, Process Creation, File Share, Detailed File Share.
- [ ] Enable command-line in 4688; enable PowerShell Script Block Logging (4104).
- [ ] Forward events (WEF/EDR) off-host; alert on 1102 (log cleared).
- [ ] SIEM rules: local-admin network logon (4624 type 3) from server subnet; admin-share access (5140 ADMIN$/C$) from non-jump host; WinRM shell creation; hacktool detections.

## Validation
- [ ] Re-run the attack after each control; confirm the expected failure (see `remediation-plan.md` validation matrix).
- [ ] Snapshot "hardened" state for repeatable before/after demos.
