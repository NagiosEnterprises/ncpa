#!/bin/bash

# Wrapper script to run cx_freeze build with proper permissions
# This script should be run from the agent directory

# Get the original user if running under sudo
get_original_user() {
    if [[ $EUID -eq 0 ]]; then
        echo ${SUDO_USER:-$USER}
    else
        echo $USER
    fi
}

# Run command as the original user (not root)
run_as_user() {
    local original_user=$(get_original_user)
    if [[ $EUID -eq 0 && -n "$SUDO_USER" ]]; then
        sudo -u "$original_user" -E "$@"
    else
        "$@"
    fi
}

# Clean any existing build directory
if [[ -d "build" ]]; then
    rm -rf build
fi

echo "Running cx_freeze build process..."
echo "Python binary: $PYTHONBIN"
echo "Current directory: $(pwd)"

# Run the freeze process with proper user permissions
if run_as_user "$PYTHONBIN" setup.py build_exe; then
    echo "Freeze build completed successfully"
    ls -la build/
else
    echo "ERROR: Freeze build failed"
    exit 1
fi
