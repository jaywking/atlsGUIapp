# ------------------------------------------
# Auto Elevation Block
# ------------------------------------------

# Relaunch this script as Administrator if not already elevated.
# Preserves any arguments (e.g., -Admin) passed to the script.

if (-not ([Security.Principal.WindowsPrincipal] 
          [Security.Principal.WindowsIdentity]::GetCurrent()
        ).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {

    # Reconstruct the argument list for the relaunch
    $argsList = @()
    foreach ($arg in $args) {
        $argsList += $arg
    }

    # Relaunch elevated
    Start-Process -FilePath "pwsh.exe" `
        -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`"", $argsList `
        -Verb RunAs

    exit
}

# ------------------------------------------
# Parameter Handling (unchanged)
# ------------------------------------------

param(
    [switch]$Admin
)


param(
    [switch]$Admin
)

# -------------------------------
# ATLSApp Launcher
# -------------------------------

# If -Admin is passed, enable DEBUG_ADMIN for this session
if ($Admin) {
    Write-Host "Admin mode enabled (DEBUG_ADMIN=true)" -ForegroundColor Cyan
    $env:DEBUG_ADMIN = "true"
} else {
    Write-Host "Admin mode not requested." -ForegroundColor DarkGray
}

# Show what DEBUG_ADMIN is *actually* set to
Write-Host "DEBUG_ADMIN is currently: $($env:DEBUG_ADMIN)" -ForegroundColor Yellow

# Optional: set your venv path here if needed
$venvPath = "$PSScriptRoot\.venv\Scripts\Activate.ps1"
$useVenv = $true
$logToFile = $false

# Move to the script directory
Set-Location -Path $PSScriptRoot

# Timestamp
$time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Banner
Write-Host ""
Write-Host "======================================="
Write-Host "   ATLSApp Local Development Launcher   "
Write-Host "======================================="
Write-Host "Time: $time"
Write-Host ""

# Activate venv
if ($useVenv -and (Test-Path $venvPath)) {
    Write-Host "Activating virtual environment..."
    . $venvPath
} else {
    Write-Host "Skipping virtual environment activation (useVenv=$useVenv)"
}
