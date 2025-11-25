# -------------------------------
# ATLSApp Launcher
# -------------------------------

# Optional: set your venv path here if needed
$venvPath = "$PSScriptRoot\.venv\Scripts\Activate.ps1"
$useVenv = $true       # set to $false to skip
$logToFile = $false    # set to $true to log to run_log.txt

# Move to the script directory
Set-Location -Path $PSScriptRoot

# Timestamp
$time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Banner
Write-Host ""
Write-Host "============================================" -ForegroundColor DarkCyan
Write-Host "        ATLSApp Development Server          " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor DarkCyan
Write-Host "Launch Time: $time"
Write-Host "Project Dir: $PSScriptRoot"
Write-Host ""

# Activate venv if enabled
if ($useVenv -and (Test-Path $venvPath)) {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    . $venvPath
    Write-Host "Venv activated."
    Write-Host ""
}
elseif ($useVenv) {
    Write-Host "Warning: virtual environment not found." -ForegroundColor Yellow
    Write-Host "Expected at: $venvPath"
    Write-Host ""
}

# Port check
$port = 8000
$portInUse = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue

if ($portInUse) {
    Write-Host "Port $port is already in use." -ForegroundColor Red
    Write-Host "Uvicorn will not start."
    Write-Host ""
    Write-Host "Press Enter to close this window..."
    Read-Host
    exit
}

# Log file path
$logFile = Join-Path $PSScriptRoot "run_log.txt"

# Uvicorn command
$uvicornCmd = "uvicorn app.main:fastapi_app --host 0.0.0.0 --port $port --reload"

Write-Host "Starting Uvicorn..." -ForegroundColor Green
Write-Host ""

if ($logToFile) {
    Write-Host "Logging enabled. Output will be written to run_log.txt"
    Write-Host ""
    Start-Process powershell -ArgumentList "-NoExit", "-Command `$($uvicornCmd) 2>&1 | Tee-Object -FilePath '$logFile'" -Wait
}
else {
    # Run in current session
    Invoke-Expression $uvicornCmd
}

# Graceful shutdown message
Write-Host ""
Write-Host "Server stopped." -ForegroundColor Yellow
Write-Host "Press Enter to close this window..."
Read-Host
