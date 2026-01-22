#!/bin/bash -e

# AIX-specific setup for NCPA build
# Integrates with virtual environment manager when available

# Virtual environment integration variables
VENV_MANAGER="${BUILD_DIR}/venv_manager.sh"
VENV_NAME="${VENV_NAME:-ncpa-build}"

# Check if using virtual environment or fallback to system Python
if [[ "$SKIP_PYTHON" == "1" ]]; then
    echo "***** aix/setup.sh - Using virtual environment mode"
    # Python will be provided by venv_manager, no system Python needed
else
    echo "***** aix/setup.sh - Fallback mode - detecting system Python"
    PYTHONBIN=$(which python3)
fi


install_prereqs() {
    echo "***** aix/setup.sh - install_prereqs()"
    echo "Installing AIX system prerequisites..."

    # --------------------------
    #  INSTALL SYSTEM REQS - PACKAGES
    # --------------------------

    if command -v dnf >/dev/null 2>&1; then
        echo "    - Detected dnf package manager."
    else
        echo "ERROR! dnf package manager not found. Please install dnf and try again."
        return 1
    fi
    
    echo "    - Installing required build packages via dnf..."
    dnf -y update
    dnf -y install sudo gcc gcc-c++ gcc-cpp make cmake automake libffi-devel

    echo "    - Assuming Python 3.12 is the target version for NCPA build"
    dnf -y install python3.12-pip python3.12-devel 

    echo "System prerequisites installation complete."

    echo "----------------------------------------"
    echo " You will need to download and compile the following manually:"
    echo " - patchelf (download source, compile, insall to /usr/local/bin)"
    echo " - cx_Freeze (download source, apply AIX patches if needed, run setup.py)"
    echo "----------------------------------------"
}

update_py_packages() {
    # Check if we're in virtual environment mode
    if [[ -n "$VENV_MANAGER" && -n "$VENV_NAME" && "$SKIP_PYTHON" == "1" ]]; then
        echo "    - Using virtual environment approach via venv_manager"
        if ! "$VENV_MANAGER" install_packages; then
            echo "ERROR! Failed to install Python packages via venv_manager"
            return 1
        fi
        
        # Get the virtual environment Python executable
        local venv_python=$("$VENV_MANAGER" get_python_path)
        if [[ -z "$venv_python" ]]; then
            echo "ERROR! Could not get virtual environment Python path"
            return 1
        fi
        
        # Update our Python commands to use the venv Python
        export PYTHONBIN="$venv_python"
        echo "    - Updated PYTHONBIN to virtual environment: $PYTHONBIN"
    else
        echo "    - Using legacy system Python approach"
        echo "Skipping update packages, manually update them with:"
        echo "$PYTHONBIN -m pip install -r $BUILD_DIR/resources/require-aix.txt --upgrade"
    fi
}

# Install cx_Freeze from source to avoid AIX wheel issues
echo "Installing cx_Freeze from source..."
# Download and extract cx_Freeze source
# Apply patches if necessary (not shown here)
# Run setup.py
# Finally use pip to install in venv
$PYTHONBIN -m pip install $BUILD_DIR/test/cx_Freeze-8.4.1

# Install patchelf directly to the system
# Download patchelf source
# Compile and install patchelf to /usr/local/bin
# Path should already be set to include /usr/local/bin


# This must be outside of install_prereqs(), so it will be executed during workflow build.

echo -e "***** aix/setup.sh - add users/groups"
set +e
mkgroup nagios
mkuser pgrp='nagios' groups='nagios' home='/home/nagios' nagios
set -e

# Automatically install Python requirements in venv after setup
echo "***** aix/setup.sh - Installing Python requirements in virtual environment if applicable"
if [ -n "$VENV_MANAGER" ] && [ -x "$VENV_MANAGER" ]; then
    "$VENV_MANAGER" install-requirements
fi
