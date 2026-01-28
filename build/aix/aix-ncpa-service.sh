#!/bin/bash

# NCPA manual start script for Solaris
# Use this if SMF service has visibility issues

NCPA_DIR="/usr/local/ncpa"
NCPA_USER="nagios"
NCPA_GROUP="nagios"
PID_FILE="$NCPA_DIR/var/run/ncpa.pid"

start_ncpa() {
    echo "Starting NCPA..."
    
    # First, ensure no NCPA processes are running
    echo "Checking for existing NCPA processes..."
    existing_pids=$(ps -ef | grep '/usr/local/ncpa/ncpa' | grep -v grep | awk '{print $2}' 2>/dev/null)
    if [ -n "$existing_pids" ]; then
        echo "Found existing NCPA processes: $existing_pids"
        echo "Stopping existing processes before starting new one..."
        stop_ncpa
        sleep 2
    fi
    
    # Check PID file
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if ps -p $pid > /dev/null 2>&1; then
            echo "NCPA is already running (PID: $pid)"
            return 1
        else
            echo "Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi
    
    # Change to NCPA directory and start
    cd "$NCPA_DIR"
    
    # Start NCPA as nagios user
    sudo -u $NCPA_USER -g $NCPA_GROUP "$NCPA_DIR/ncpa" --start
    
    if [ $? -eq 0 ]; then
        echo "NCPA started successfully"
        echo "Check status with: ps -ef | grep ncpa"
        echo "Check logs in: $NCPA_DIR/var/log/"
    else
        echo "Failed to start NCPA"
        return 1
    fi
}

stop_ncpa() {
    echo "Stopping NCPA..."
    
    # First try to stop using PID file
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping NCPA process $pid..."
            kill $pid
            sleep 2
            
            # Check if it's still running
            if ps -p $pid > /dev/null 2>&1; then
                echo "Process still running, forcing termination..."
                kill -9 $pid 2>/dev/null
            fi
            echo "NCPA stopped (PID: $pid)"
        fi
        rm -f "$PID_FILE"
    fi
    
    # Always do comprehensive cleanup of all NCPA processes
    echo "Performing comprehensive NCPA process cleanup..."
    
    # Find and kill all NCPA processes more thoroughly
    for pattern in "/usr/local/ncpa/ncpa" "ncpa" "$NCPA_DIR/ncpa"; do
        pids=$(ps -ef | grep '/usr/local/ncpa/ncpa' | grep -v grep | awk '{print $2}' 2>/dev/null)
        if [ -n "$pids" ]; then
            echo "Found NCPA processes with pattern '$pattern': $pids"
            for pid in $pids; do
                echo "Stopping process $pid..."
                kill $pid 2>/dev/null
                sleep 1
                
                # Force kill if still running
                if ps -p $pid > /dev/null 2>&1; then
                    echo "Force killing process $pid..."
                    kill -9 $pid 2>/dev/null
                fi
            done
        fi
    done
    
    # Wait a moment and verify cleanup
    sleep 2
    remaining=$(ps -ef | grep '/usr/local/ncpa/ncpa' | grep -v grep | awk '{print $2}' 2>/dev/null | wc -l)
    if [ "$remaining" -gt 0 ]; then
        echo "Warning: $remaining NCPA processes may still be running"
        echo "Remaining processes:"
        ps -ef | grep ncpa | grep -v grep
    else
        echo "All NCPA processes stopped successfully"
    fi
    
    # Clean up any remaining PID files
    rm -f "$PID_FILE" 2>/dev/null
    rm -f "$NCPA_DIR/var/run"/*.pid 2>/dev/null

    # Exit after stopping
    echo "Process stopped."
    exit 0
}

killall_ncpa() {
    echo "Performing aggressive cleanup of ALL NCPA processes..."
    
    # Find and display all NCPA-related processes
    echo "Current NCPA processes:"
    ps -ef | grep -i ncpa | grep -v grep
    
    # Kill all NCPA processes aggressively
    for pattern in "/usr/local/ncpa/ncpa" "ncpa" "/usr/local/ncpa"; do
        pids=$(ps -ef | grep '/usr/local/ncpa/ncpa' | grep -v grep | awk '{print $2}' 2>/dev/null)
        if [ -n "$pids" ]; then
            echo "Killing processes matching '$pattern': $pids"
            for pid in $pids; do
                kill -9 $pid 2>/dev/null || true
            done
        fi
    done
    
    # Clean up all PID files
    rm -f "$PID_FILE" 2>/dev/null
    rm -f "$NCPA_DIR/var/run"/*.pid 2>/dev/null
    rm -f /var/lock/subsys/ncpa 2>/dev/null
    
    sleep 1
    
    # Verify cleanup
    remaining=$(ps -ef | grep -i ncpa | grep -v grep | wc -l)
    if [ "$remaining" -eq 0 ]; then
        echo "All NCPA processes have been terminated"
    else
        echo "Warning: Some NCPA processes may still be running:"
        ps -ef | grep -i ncpa | grep -v grep
    fi

    # Exit after stopping
    echo "Process stopped."
    exit 0
}

# Trap signals
# Trap SIGTERM (standard termination signal)
# to call the stop_process function.
trap 'stop_ncpa' 15

# Trap SIGKILL to perform a forced stop
trap 'killall_ncpa' 9

# Start the process initially
start_ncpa

# Allow some time for NCPA to initialize
sleep 15

# Wait in a loop for signals to be received
# The trap commands above will interrupt this wait.
echo "Manager is now waiting for signals. PID: $$"

# Monitor NCPA processes
ncpa_running=true
while ncpa_running; do

    # Optional: Check if NCPA process is still running
    # ncpa_process_count=$(ps -ef | grep ncpa | grep start | wc -l)
    # if [ ncpa_process_count -ne 3 ]; then
    #     echo "NCPA process has stopped unexpectedly, exiting manager."
    #     ncpa_running=false
    #     exit 1
    # fi

    sleep 60
done