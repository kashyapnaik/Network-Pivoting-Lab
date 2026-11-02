# Windows Audit Policy Setup (for the Target)

By default Windows does **not** log everything the detections in
`blue-team-detection-guide.md` rely on (notably process command lines and
detailed file-share access). Enable these on WIN-TARGET01 (admin PowerShell).

> These are **detective** controls — they don't block the attack, they make it
> visible. Run them so the Event IDs actually populate.

## 1. Enable the audit subcategories

```powershell
# Logon / Logoff (4624/4625/4634/4648)
auditpol /set /subcategory:"Logon" /success:enable /failure:enable
auditpol /set /subcategory:"Logoff" /success:enable
auditpol /set /subcategory:"Special Logon" /success:enable      # 4672

# Detailed Tracking — process creation (4688)
auditpol /set /subcategory:"Process Creation" /success:enable

# Object Access — file share (5140) and detailed file share (5145)
auditpol /set /subcategory:"File Share" /success:enable /failure:enable
auditpol /set /subcategory:"Detailed File Share" /success:enable

# Verify
auditpol /get /category:* | findstr /i "Logon Process File"
```

## 2. Include the command line in 4688 events

```powershell
# Registry: log the full command line of created processes
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Audit" `
  /v ProcessCreationIncludeCmdLine_Enabled /t REG_DWORD /d 1 /f
```

## 3. Turn on PowerShell logging

```powershell
# Script Block Logging (Event 4104) + Module Logging
$base = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell"
New-Item -Path "$base\ScriptBlockLogging" -Force | Out-Null
Set-ItemProperty -Path "$base\ScriptBlockLogging" -Name EnableScriptBlockLogging -Value 1
New-Item -Path "$base\ModuleLogging" -Force | Out-Null
Set-ItemProperty -Path "$base\ModuleLogging" -Name EnableModuleLogging -Value 1
```

## 4. Where to read the results

| Signal | Log |
|---|---|
| 4624/4625/4672/4688/5140/5145/5156 | **Windows Logs → Security** |
| WinRM remote shells | **Applications and Services → Microsoft → Windows → WinRM/Operational** |
| PowerShell 4104 | **… → Windows → PowerShell/Operational** |
| Defender detections | **… → Windows → Windows Defender/Operational** |

Quick query example (PowerShell):
```powershell
# Network logons (type 3) in the last hour
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624; StartTime=(Get-Date).AddHours(-1)} |
  Where-Object { $_.Message -match 'Logon Type:\s+3' } |
  Select-Object TimeCreated, @{n='User';e={($_.Message -split 'Account Name:\s+')[2] -split '\r' | Select -First 1}}
```

## 5. Forward to a central collector (optional)

For a real SOC, enable **Windows Event Forwarding (WEF)** to a collector, or an
EDR agent, so these events leave the (potentially compromised) host. Locally
stored logs can be cleared by an attacker with admin — which itself generates
**Event ID 1102 (audit log cleared)**, another thing to alert on.
