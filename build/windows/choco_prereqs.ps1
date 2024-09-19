<#
    choco_prereqs.ps1

    This script downloads and installs Chocolatey and the necessary
    prerequisites to build Python with a custom OpenSSL version
    as well as the necessary prerequisites to build NCPA.
#>

### 1. Chocolatey Script
## 1.0 Install Chocolatey
## 1.1 Install Git, Perl and Visual Studio Build Tools with Chocolatey
# Force PowerShell to use TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$sysBGColor = [System.Console]::BackgroundColor
$sysFGColor = [System.Console]::ForegroundColor
$colorBGmain = "Black"
$colorFGmain = "Yellow"
$colorBGsub = "Black"
$colorFGsub = "White"

[System.Console]::BackgroundColor = $colorBGmain
[System.Console]::ForegroundColor = $colorFGmain
Write-Host "Running Chocolatey install script..."
[System.Console]::BackgroundColor = $colorBGsub
[System.Console]::ForegroundColor = $colorFGsub

# Force PowerShell to use TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

### 1. Install Chocolatey
try {
    choco -v
    Write-Host "Chocolatey already installed, passing..."
} catch {
    Write-Host "Installing Chocolatey..."
    Set-ExecutionPolicy Bypass -Scope Process -Force;
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
}

# Add Chocolatey to system path just in case
[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "Machine") + ";C:\ProgramData\chocolatey\bin", "Machine")

### 2. Install Git, Perl and Visual Studio Build Tools
Write-Host "Chocolatey installing prerequisites"
choco feature enable -name=exitOnRebootDetected
if(-not (Get-Command git    -ErrorAction SilentlyContinue)){ choco install git -y }
if(-not (Get-Command perl   -ErrorAction SilentlyContinue)){ choco install strawberryperl -y }
if(-not (Get-Command nasm   -ErrorAction SilentlyContinue)){ choco install nasm -y }
if(-not (Get-Command nsis   -ErrorAction SilentlyContinue)){ choco install nsis -y }

choco install python --version=3.12.6 -y --force
#choco install visualstudio2019buildtools --package-parameters "--add Microsoft.VisualStudio.Workload.VCTools;includeRecommended" -y
choco install visualstudio2022buildtools -y --package-parameters "--add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 --add Microsoft.VisualStudio.Component.Windows10SDK.19041 --add Microsoft.VisualStudio.Component.Windows10SDK.18362"
choco install visualstudio2022community -y --package-parameters "--add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 --add Microsoft.VisualStudio.Component.Windows10SDK.19041 --add Microsoft.VisualStudio.Component.Windows10SDK.18362"

Write-Host "----------------------------------------"
Write-Host "Chocolatey install script complete"
Write-Host "----------------------------------------"

Import-Module $env:ChocolateyInstall\helpers\chocolateyProfile.psm1
refreshenv

# Add Perl, NASM, Git, etc. to the PATH
[System.Console]::BackgroundColor = $colorBGmain
[System.Console]::ForegroundColor = $colorFGmain
Write-Host "Adding prerequisites to PATH"
$env:Path += ";C:\Strawberry\perl\bin"
$env:Path += ";C:\Program Files\NASM"
$env:Path += ";C:\Program Files\Git\bin"
$env:Path += ";C:\Program Files\NSIS" # it should only be in Program Files (x86) but I want to be sure it's in the path
$env:Path += ";C:\Program Files (x86)\NSIS"
# $env:Path += ";C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin"
$env:Path += ";C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin"

# Import-Module $env:ChocolateyInstall\helpers\chocolateyProfile.psm1
# refreshenv
$rebootRequired = $false

# Check for Component-Based Servicing registry key
if (Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending") {
    $rebootRequired = $true
}
# Check for Windows Update registry key
if (Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired") {
    $rebootRequired = $true
}
# Check for PendingFileRenameOperations registry key
$pendingFileRename = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager" -Name PendingFileRenameOperations -ErrorAction SilentlyContinue
if ($pendingFileRename) {
    $rebootRequired = $true
}
if ($rebootRequired) {
    Write-Host "A system reboot is pending. Exiting..."
    exit 1
}


[System.Console]::BackgroundColor = $sysBGColor
[System.Console]::ForegroundColor = $sysFGColor
