param(
    [string]$ListenHost = "0.0.0.0",
    [int]$Port = 8000,
    [switch]$Reload
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
$logDir = Join-Path $projectRoot "logs"
$logPath = Join-Path $logDir "uvicorn_facilities.log"

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$argsList = @("app.main:fastapi_app", "--host", $ListenHost, "--port", $Port)
if ($Reload) { $argsList += "--reload" }

Write-Host "Logging uvicorn output to $logPath" -ForegroundColor Cyan
Write-Host "Command: uvicorn $($argsList -join ' ')" -ForegroundColor Cyan

uvicorn @argsList *>&1 | Tee-Object -FilePath $logPath
