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
    #  INSTALL SYSTEM PREREQS - PACKAGES
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

    echo "Building and installing additional tools from source..."
    build_cxFreeze
    build_patchelf

    echo "AIX system prerequisites installation finished."
}

#
# update_py_packages() {
#     # Check if we're in virtual environment mode
#     if [[ -n "$VENV_MANAGER" && -n "$VENV_NAME" && "$SKIP_PYTHON" == "1" ]]; then
#         echo "    - Using virtual environment approach via venv_manager"
#         if ! "$VENV_MANAGER" install_packages; then
#             echo "ERROR! Failed to install Python packages via venv_manager"
#             return 1
#         fi
        
#         # Get the virtual environment Python executable
#         local venv_python=$("$VENV_MANAGER" get_python_path)
#         if [[ -z "$venv_python" ]]; then
#             echo "ERROR! Could not get virtual environment Python path"
#             return 1
#         fi
        
#         # Update our Python commands to use the venv Python
#         export PYTHONBIN="$venv_python"
#         echo "    - Updated PYTHONBIN to virtual environment: $PYTHONBIN"
#     else
#         echo "    - Using legacy system Python approach"
#         echo "Skipping update packages, manually update them with:"
#         echo "$PYTHONBIN -m pip install -r $BUILD_DIR/resources/require-aix.txt --upgrade"
#     fi
# }

build_cxFreeze() {
    # Install cx_Freeze from source to avoid AIX wheel issues
    echo "Installing cx_Freeze from source..."

    # Check if cx_Freeze is already installed
    if $PYTHONBIN -m pip show cx_Freeze >/dev/null 2>&1; then
        echo "cx_Freeze is already installed. Skipping build."
        return 0
    fi

    # Otherwise, proceed to download and build cx_Freeze

    # Download and extract cx_Freeze source
    wget https://github.com/marcelotduarte/cx_Freeze/archive/refs/tags/8.4.1.tar.gz -O /tmp/cx_Freeze-8.4.1.tar.gz

    if [ ! -f "/tmp/cx_Freeze-8.4.1.tar.gz" ]; then
        echo "ERROR! cx_Freeze source tarball not found."
        return 1
    else
        echo "cx_Freeze source tarball downloaded."
    fi

    gunzip -c /tmp/cx_Freeze-8.4.1.tar.gz | tar -xvf -

    if [ ! -d "cx_Freeze-8.4.1" ]; then
        echo "ERROR! cx_Freeze source directory not found after extraction."
        return 1
    else
        echo "cx_Freeze source directory found."
    fi

    echo "Changing to cx_Freeze source directory..."
    cd cx_Freeze-8.4.1

    # Copy cx_Freeze AIX setup patch
    echo "Applying AIX-specific setup patch for cx_Freeze..."
    cp -f "$BUILD_DIR/aix/setup_cxFreeze_aix.py" "$BUILD_DIR/cx_Freeze-8.4.1/setup.py"
    
    # Build cx_Freeze, we should be in the venv
    echo "Building cx_Freeze with AIX patch..."
    $PYTHONBIN setup.py build

    # Finally use pip to install in venv
    echo "Installing cx_Freeze into the environment..."
    $PYTHONBIN -m pip install $BUILD_DIR/cx_Freeze-8.4.1

    # Return to original directory
    cd ..
}

build_patchelf() {
    echo "Building and installing patchelf from source..."

    # Check if patchelf is already installed
    if command -v /usr/local/bin/patchelf >/dev/null 2>&1; then
        echo "patchelf is already installed. Skipping build."
        return 0
    fi

    # Otherwise, proceed to download and build patchelf

    # Download patchelf source
    wget https://github.com/NixOS/patchelf/releases/download/0.18.0/patchelf-0.18.0.tar.gz -O /tmp/patchelf-0.18.0.tar.gz

    if [ ! -f "/tmp/patchelf-0.18.0.tar.gz" ]; then
        echo "ERROR! patchelf source tarball not found."
        return 1
    else
        echo "patchelf source tarball downloaded."
    fi

    gunzip -c /tmp/patchelf-0.18.0.tar.gz | tar -xvf -

    if [ ! -d "patchelf-0.18.0" ]; then
        echo "ERROR! patchelf source directory not found after extraction."
        return 1
    else
        echo "patchelf source directory found."
    fi

    echo "Changing to patchelf source directory..."
    cd patchelf-0.18.0

    # Configure, compile, and install patchelf
    echo "bootstraping patchelf..."
    ./bootstrap.sh

    echo "Configuring patchelf..."
    ./configure --prefix=/usr/local

    # Compile patchelf
    echo "Compiling patchelf..."
    make
    echo "Installing patchelf to /usr/local/bin..."
    make install

    # verify installation
    if command -v /usr/local/bin/patchelf >/dev/null 2>&1; then
        echo "patchelf installed successfully."
    else
        echo "ERROR! patchelf installation failed."
        return 1
    fi

    # Return to original directory
    cd ..
}


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
