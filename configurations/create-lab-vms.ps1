<#
=====================================================================
 create-lab-vms.ps1  —  Phase 2/3 builder for the Network Pivoting Lab
=====================================================================
 Creates three EMPTY VM shells and wires them to two isolated
 VirtualBox Internal Networks. It does NOT install any OS.

 SAFETY:
   - Refuses to touch any VM it did not create (name allow-list).
   - Skips a VM that already exists instead of overwriting it.
   - Uses ONLY VirtualBox "intnet" adapters => no bridge/NAT, so the
     lab VMs have no path to your home Wi-Fi or the internet.

 Run from an ordinary PowerShell (no admin needed for VBoxManage):
   .\create-lab-vms.ps1
=====================================================================
#>

$ErrorActionPreference = "Stop"
$VBox   = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
$Folder = (& $VBox list systemproperties | Select-String "Default machine folder").ToString().Split(":",2)[1].Trim()

# --- VMs this script is ALLOWED to create. Anything else is off-limits. ---
$Lab = @(
  @{ Name="KALI-ATTACKER"; OS="Debian_64";    Cpu=2; Mem=3072; Vram=32;  DiskMB=40960; Nic1="DMZ-NET";      Nic2=$null         }
  @{ Name="PIVOT01";       OS="Ubuntu_64";    Cpu=1; Mem=1536; Vram=16;  DiskMB=20480; Nic1="DMZ-NET";      Nic2="INTERNAL-NET" }
  @{ Name="WIN-TARGET01";  OS="Windows10_64"; Cpu=2; Mem=4096; Vram=128; DiskMB=51200; Nic1="INTERNAL-NET"; Nic2=$null         }
)

function New-LabVM($v) {
  $existing = (& $VBox list vms) -match "`"$($v.Name)`""
  if ($existing) { Write-Host "[skip] $($v.Name) already exists." -ForegroundColor Yellow; return }

  $disk = Join-Path $Folder "$($v.Name)\$($v.Name).vdi"
  Write-Host "[create] $($v.Name)" -ForegroundColor Cyan

  # createvm      : defines the VM and writes its .vbox file (--register adds it to VirtualBox)
  & $VBox createvm --name $v.Name --ostype $v.OS --register

  # modifyvm      : CPU, RAM, video RAM, boot order (DVD first for the installer, then disk).
  #                 clipboard/drag-drop disabled = isolation hygiene between host and lab guest.
  & $VBox modifyvm $v.Name --cpus $v.Cpu --memory $v.Mem --vram $v.Vram `
        --boot1 dvd --boot2 disk --boot3 none --boot4 none `
        --clipboard-mode disabled --draganddrop disabled

  # NIC1: intnet  : an Internal Network is a private L2 switch shared ONLY by VMs that name it.
  #                 It is isolated from the host and the internet by design.
  & $VBox modifyvm $v.Name --nic1 intnet --intnet1 $v.Nic1 --nictype1 82540EM --cableconnected1 on --nicpromisc1 deny

  if ($v.Nic2) {
    & $VBox modifyvm $v.Name --nic2 intnet --intnet2 $v.Nic2 --nictype2 82540EM --cableconnected2 on --nicpromisc2 deny
    & $VBox modifyvm $v.Name --nic3 none --nic4 none
  } else {
    & $VBox modifyvm $v.Name --nic2 none --nic3 none --nic4 none
  }

  # Storage: a SATA (AHCI) controller, a dynamic VDI disk on port 0, an empty DVD on port 1.
  & $VBox createmedium disk --filename $disk --size $v.DiskMB --format VDI
  & $VBox storagectl $v.Name --name "SATA" --add sata --controller IntelAhci --portcount 2 --bootable on
  & $VBox storageattach $v.Name --storagectl "SATA" --port 0 --device 0 --type hdd --medium $disk
  & $VBox storageattach $v.Name --storagectl "SATA" --port 1 --device 0 --type dvddrive --medium emptydrive

  Write-Host "[ok]     $($v.Name) created." -ForegroundColor Green
}

foreach ($vm in $Lab) { New-LabVM $vm }

Write-Host "`n===== Resulting topology =====" -ForegroundColor Cyan
foreach ($vm in $Lab) {
  $i = & $VBox showvminfo $vm.Name --machinereadable
  $n2 = ($i | Select-String '^intnet2=')
  $n2 = if ($n2) { ($n2 -replace '.*="?([^"]*)"?','$1') } else { "-" }
  "{0,-15} NIC1={1,-13} NIC2={2}" -f $vm.Name, $vm.Nic1, $n2
}
