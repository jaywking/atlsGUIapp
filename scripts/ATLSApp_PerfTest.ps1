# ATLSApp – Performance Test Script (ASCII-safe)
# Prints results AND writes them to a timestamped log file.
# Jay King • Above The Line Safety

$base = "http://127.0.0.1:8000/api/locations"

# Create log directory if needed
$logDir = Join-Path $PSScriptRoot "perf_logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

# Timestamped log file
$timestamp = (Get-Date).ToString("yyyy-MM-dd_HH-mm-ss")
$logFile = Join-Path $logDir "perf_test_$timestamp.log"

function Write-Log {
    param([string]$text)
    Add-Content -Path $logFile -Value $text
}

function Run-Test($label, $method, $url) {

    $header = "`n=== $label ==="
    Write-Host $header -ForegroundColor Cyan
    Write-Log  $header

    $start = Get-Date
    try {
        if ($method -eq "GET") {
            $response = Invoke-RestMethod -Uri $url -Method GET
        } else {
            $response = Invoke-RestMethod -Uri $url -Method POST
        }
    } catch {
        Write-Host "ERROR: $_" -ForegroundColor Red
        Write-Log  "ERROR: $_"
        return
    }

    $stop = Get-Date
    $ms = [int](($stop - $start).TotalMilliseconds)

    $timeLine = "Time: $ms ms"
    Write-Host $timeLine -ForegroundColor Yellow
    Write-Log  $timeLine

    # Print and log response fields if present
    if ($response.duration_ms) {
        $s = "duration_ms (reported): $($response.duration_ms)"
        Write-Host $s; Write-Log $s
    }
    if ($response.avg_per_record_ms) {
        $s = "avg_per_record_ms (reported): $($response.avg_per_record_ms)"
        Write-Host $s; Write-Log $s
    }
    if ($response.reviewed) {
        $s = "Reviewed: $($response.reviewed)"
        Write-Host $s; Write-Log $s
    }
    if ($response.matched -ne $null) {
        $s = "Matched: $($response.matched)"
        Write-Host $s; Write-Log $s
    }
    if ($response.unresolved -ne $null) {
        $s = "Unresolved: $($response.unresolved)"
        Write-Host $s; Write-Log $s
    }
    if ($response.conflicts -ne $null) {
        $s = "Conflicts: $($response.conflicts)"
        Write-Host $s; Write-Log $s
    }

    # Save full raw JSON (compact) for inspection
    $json = $response | ConvertTo-Json -Compress
    Write-Log "RAW_JSON: $json"

    return $response
}

Write-Host "Starting ATLSApp Performance Tests..." -ForegroundColor Green
Write-Log  "Starting ATLSApp Performance Tests..."
Write-Log  "Log file: $logFile"
Write-Log  "Timestamp: $timestamp"

Run-Test "COLD - GET /locations/all?refresh=true" "GET" "$base/all?refresh=true"
Run-Test "WARM - GET /locations/all" "GET" "$base/all"
Run-Test "MATCH - POST /locations/match_all" "POST" "$base/match_all"
Run-Test "MATCH FORCE - POST /locations/match_all?force=true" "POST" "$base/match_all?force=true"
Run-Test "MATCH FULL RELOAD - POST /locations/match_all?refresh=true" "POST" "$base/match_all?refresh=true"

Write-Host "`nAll tests completed." -ForegroundColor Green
Write-Log  "`nAll tests completed."
Write-Log  "-------------------------------------------------------------"
