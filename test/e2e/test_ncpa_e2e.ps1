# Stop on first error
$ErrorActionPreference = "Stop"

# --- Configuration (Defaults via Env Vars or local fallbacks) ---
$NcpaHost  = if ($env:NCPA_HOST)  { $env:NCPA_HOST }  else { "localhost" }
$NcpaPort  = if ($env:NCPA_PORT)  { $env:NCPA_PORT }  else { "5693" }
$NcpaToken = if ($env:NCPA_TOKEN) { $env:NCPA_TOKEN } else { "8675309" }

$BaseUrl = "https://${NcpaHost}:${NcpaPort}/api"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Starting NCPA E2E Verification Suite"     -ForegroundColor Cyan
Write-Host " Target: $BaseUrl"                         -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Trust self-signed certificates (Common for local/test NCPA agents)
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }

# -------------------------------------------------------------------
# 1. Health Check / Ping API
# -------------------------------------------------------------------
Write-Host -NoNewline "[1/4] Testing API Connectivity & Auth... "
try {
    $uri = "${BaseUrl}/system/agent_version?token=${NcpaToken}"
    $response = Invoke-RestMethod -Uri $uri -Method Get -SkipCertificateCheck
    
    # Debug response
    Write-Host "Debug: $($response | ConvertTo-Json)" -ForegroundColor Yellow

    if ($response.agent_version) {
        Write-Host "SUCCESS (Version: $($response.agent_version))" -ForegroundColor Green
    } else {
        throw "Response received, but 'agent_version' field missing."
    }
} catch {
    Write-Host "FAILED" -ForegroundColor Red
    Write-Error $_
    exit 1
}

# -------------------------------------------------------------------
# 2. Check Built-in Metric (CPU Usage)
# -------------------------------------------------------------------
Write-Host -NoNewline "[2/4] Querying System Metric (CPU Percent)... "
try {
    $uri = "${BaseUrl}/cpu/percent?token=${NcpaToken}"
    $response = Invoke-RestMethod -Uri $uri -Method Get -SkipCertificateCheck

    if ($null -ne $response.percent) {
        Write-Host "SUCCESS" -ForegroundColor Green
    } else {
        throw "JSON response missing 'percent' field."
    }
} catch {
    Write-Host "FAILED" -ForegroundColor Red
    Write-Error $_
    exit 1
}

# -------------------------------------------------------------------
# 3. Test Active Check API with Thresholds (Logical Disk)
# -------------------------------------------------------------------
Write-Host -NoNewline "[3/4] Testing Active Check Endpoint with Thresholds... "
try {
    # Querying drive C on Windows
    $uri = "${BaseUrl}/disk/logical/C:|/used_percent?token=${NcpaToken}&check=true&warning=80&critical=90"
    $response = Invoke-RestMethod -Uri $uri -Method Get -SkipCertificateCheck

    # NCPA active check endpoints return structured JSON with a 'returncode' (0=OK, 1=WARN, 2=CRIT)
    if ($null -ne $response.returncode) {
        Write-Host "SUCCESS (Exit Code: $($response.returncode))" -ForegroundColor Green
    } else {
        throw "Active check response missing 'returncode' property."
    }
} catch {
    Write-Host "FAILED" -ForegroundColor Red
    Write-Error $_
    exit 1
}

# -------------------------------------------------------------------
# 4. Execute Custom Plugin Check
# -------------------------------------------------------------------
Write-Host -NoNewline "[4/4] Executing External Plugin via API... "
try {
    # Assumes 'check_os.ps1' or similar plugin exists in NCPA's plugins folder
    $uri = "${BaseUrl}/plugins/check_os.ps1?token=${NcpaToken}"
    $response = Invoke-RestMethod -Uri $uri -Method Get -SkipCertificateCheck

    if ($null -ne $response.returncode) {
        Write-Host "SUCCESS (Plugin output: '$($response.stdout.Trim())')" -ForegroundColor Green
    } else {
        throw "Plugin runner response missing 'returncode' property."
    }
} catch {
    Write-Host "FAILED" -ForegroundColor Red
    Write-Error $_
    exit 1
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " All NCPA E2E Tests Passed Successfully! " -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan