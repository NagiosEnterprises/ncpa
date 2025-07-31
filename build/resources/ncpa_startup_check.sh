#!/bin/bash

# NCPA Startup Check Script for macOS
# This script ensures NCPA starts properly and stays running

NCPA_HOME="/usr/local/ncpa"
NCPA_SERVICE="com.nagios.ncpa"
LOG_FILE="$NCPA_HOME/var/log/ncpa_startup_check.log"
MAX_RETRIES=3
RETRY_DELAY=5

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

check_ncpa_running() {
    if launchctl list | grep -q "$NCPA_SERVICE"; then
        local pid=$(launchctl list | grep "$NCPA_SERVICE" | awk '{print $1}')
        if [[ "$pid" != "-" ]] && [[ "$pid" =~ ^[0-9]+$ ]]; then
            return 0  # Running
        fi
    fi
    return 1  # Not running
}

start_ncpa() {
    log_message "Attempting to start NCPA service..."
    
    # Ensure the service is loaded
    if [[ -f "/Library/LaunchDaemons/${NCPA_SERVICE}.plist" ]]; then
        launchctl load "/Library/LaunchDaemons/${NCPA_SERVICE}.plist" 2>/dev/null || true
    fi
    
    # Start the service
    launchctl start "$NCPA_SERVICE" 2>/dev/null || true
    
    # Wait a moment for startup
    sleep 2
    
    if check_ncpa_running; then
        log_message "NCPA service started successfully"
        return 0
    else
        log_message "Failed to start NCPA service"
        return 1
    fi
}

# Main startup check logic
log_message "Starting NCPA startup check..."

retry_count=0
while [[ $retry_count -lt $MAX_RETRIES ]]; do
    if check_ncpa_running; then
        log_message "NCPA is running properly"
        exit 0
    else
        log_message "NCPA is not running (attempt $((retry_count + 1))/$MAX_RETRIES)"
        
        if start_ncpa; then
            break
        fi
        
        retry_count=$((retry_count + 1))
        if [[ $retry_count -lt $MAX_RETRIES ]]; then
            log_message "Waiting $RETRY_DELAY seconds before retry..."
            sleep $RETRY_DELAY
        fi
    fi
done

if [[ $retry_count -eq $MAX_RETRIES ]]; then
    log_message "Failed to start NCPA after $MAX_RETRIES attempts"
    exit 1
fi

log_message "NCPA startup check completed successfully"
exit 0
