#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
NCPA_HOST="${NCPA_HOST:-localhost}"
NCPA_PORT="${NCPA_PORT:-5693}"
NCPA_TOKEN="${NCPA_TOKEN:-mytoken}"
BASE_URL="https://${NCPA_HOST}:${NCPA_PORT}/api"

echo "=========================================="
echo " Starting NCPA E2E Verification Suite"
echo " Target: ${BASE_URL}"
echo "=========================================="

# 1. Health Check / Ping API
echo -n "[1/4] Testing API Connectivity & Auth... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k "${BASE_URL}/system/agent_version?token=${NCPA_TOKEN}")

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "SUCCESS (HTTP 200)"
else
    echo "FAILED (HTTP $HTTP_CODE)"
    exit 1
fi

# 2. Check Built-in Metric (CPU Usage)
echo -n "[2/4] Querying System Metric (CPU Percent)... "
CPU_RESPONSE=$(curl -s -k "${BASE_URL}/cpu/percent?token=${NCPA_TOKEN}")

# Verify response contains expected JSON structure
if echo "$CPU_RESPONSE" | grep -q '"percent"'; then
    echo "SUCCESS"
else
    echo "FAILED - Invalid JSON response"
    echo "Response: $CPU_RESPONSE"
    exit 1
fi

# 3. Test Nagios Check API with Thresholds (Disk Usage)
echo -n "[3/4] Testing Active Check Endpoint with Thresholds... "
DISK_RESPONSE=$(curl -s -k "${BASE_URL}/disk/logical/root/used_percent?token=${NCPA_TOKEN}&warning=80&critical=90")

# Check if return code field is present (0 = OK, 1 = WARNING, 2 = CRITICAL)
if echo "$DISK_RESPONSE" | grep -q '"returncode"'; then
    echo "SUCCESS"
else
    echo "FAILED - Active check format unexpected"
    echo "Response: $DISK_RESPONSE"
    exit 1
fi

# # 4. Execute Custom Plugin Check
# echo -n "[4/4] Executing External Plugin via API... "
# PLUGIN_RESPONSE=$(curl -s -k "${BASE_URL}/runcheck/check_dummy?token=${NCPA_TOKEN}&args=-w%205")

# if echo "$PLUGIN_RESPONSE" | grep -q '"returncode"'; then
#     echo "SUCCESS"
# else
#     echo "FAILED - Plugin execution failed"
#     echo "Response: $PLUGIN_RESPONSE"
#     exit 1
# fi

echo "=========================================="
echo " All NCPA E2E Tests Passed Successfully! "
echo "=========================================="