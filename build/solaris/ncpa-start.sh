#!/bin/bash

# NCPA manual start script for Solaris
# Use this if SMF service has visibility issues

NCPA_DIR="/usr/local/ncpa"
NCPA_USER="nagios"
NCPA_GROUP="nagios"
PID_FILE="$NCPA_DIR/var/run/ncpa.pid"

start_ncpa() {
    echo "Starting NCPA..."
    
    # Check if already running
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
    
    # Set environment
    export LD_LIBRARY_PATH="$NCPA_DIR/lib:/usr/local/lib:/lib:/usr/lib"
    export PATH="/usr/local/bin:/usr/bin:/bin"
    
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
    
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid
            echo "NCPA stopped (PID: $pid)"
            rm -f "$PID_FILE"
        else
            echo "NCPA process not found, removing PID file"
            rm -f "$PID_FILE"
        fi
    else
        # Try to find and kill NCPA processes
        pkill -f "ncpa"
        echo "Killed any running NCPA processes"
    fi
}

status_ncpa() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if ps -p $pid > /dev/null 2>&1; then
            echo "NCPA is running (PID: $pid)"
            return 0
        else
            echo "NCPA is not running (stale PID file)"
            return 1
        fi
    else
        echo "NCPA is not running"
        return 1
    fi
}

case "$1" in
    start)
        start_ncpa
        ;;
    stop)
        stop_ncpa
        ;;
    restart)
        stop_ncpa
        sleep 2
        start_ncpa
        ;;
    status)
        status_ncpa
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
