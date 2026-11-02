<#
 download-isos.ps1 — download Kali + Ubuntu ISOs and verify SHA256.
 Uses curl.exe (resume-capable). Fails loudly if a hash does not match.
#>
$ErrorActionPreference = "Stop"
$dest = "C:\Users\naikk\VirtualBox VMs\_ISOs"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$downloads = @(
  @{ Name="Kali 2026.3 installer";
     Url ="https://cdimage.kali.org/kali-2026.3/kali-linux-2026.3-installer-amd64.iso";
     File="$dest\kali-linux-2026.3-installer-amd64.iso";
     Sha ="db9cbed33edb45727d16911813c2434fcd1419585007884153be22a03b30ec2f" }
  @{ Name="Ubuntu 24.04.5 live-server";
     Url ="https://releases.ubuntu.com/24.04.5/ubuntu-24.04.5-live-server-amd64.iso";
     File="$dest\ubuntu-24.04.5-live-server-amd64.iso";
     Sha ="97f3d7ffb032c3eb3b23d2c8be9cc76e60c2c1f2c0146ba5ba9fe01cafae0fd8" }
)

$results = @()
foreach ($d in $downloads) {
  Write-Output "========================================================"
  Write-Output "Downloading: $($d.Name)"
  Write-Output "  -> $($d.File)"
  # -L follow redirects (mirrors), -C - resume if partially present, --retry transient errors
  & curl.exe -L -C - --retry 5 --retry-delay 5 -o $d.File $d.Url
  if (-not (Test-Path $d.File)) { Write-Output "[FAIL] file not created"; $results += "FAIL  $($d.Name) (no file)"; continue }

  Write-Output "Verifying SHA256..."
  $actual = (Get-FileHash $d.File -Algorithm SHA256).Hash.ToLower()
  if ($actual -eq $d.Sha) {
    $sizeGB = [math]::Round((Get-Item $d.File).Length/1GB,2)
    Write-Output "[OK]   hash matches ($sizeGB GB)"
    $results += "OK    $($d.Name)  ($sizeGB GB)"
  } else {
    Write-Output "[FAIL] HASH MISMATCH"
    Write-Output "  expected: $($d.Sha)"
    Write-Output "  actual:   $actual"
    $results += "FAIL  $($d.Name) (hash mismatch)"
  }
}

Write-Output "`n==================== SUMMARY ===================="
$results | ForEach-Object { Write-Output $_ }
Write-Output "ISO folder: $dest"
