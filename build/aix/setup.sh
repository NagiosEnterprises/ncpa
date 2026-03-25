#!/bin/bash -e

# AIX-specific setup for NCPA build
# Integrates with virtual environment manager when available

# Virtual environment integration variables
VENV_MANAGER="${BUILD_DIR}/venv_manager.sh"
VENV_NAME="${VENV_NAME:-ncpa-build}"

# Export necessary build environment variables
export MAKE="gmake"
export CC="gcc"

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
    dnf -y install sudo gcc gcc-c++ gcc-cpp make cmake automake libffi-devel rust cargo

    # Ensure Python 3.12 is installed
    if command -v python3.12 >/dev/null 2>&1; then
        echo "    - Detected Python 3.12 installation."
    else
        echo "ERROR! Python 3.12 not found. Please install Python 3.12 from IBM AIX Toolbox and try again."
        return 1
    fi

    echo "    - Assuming Python 3.12 is the target version for NCPA build"
    dnf -y install python3.12-pip python3.12-devel

    echo "----------------------------------------"
    echo "Adding additional tools from source..."
    build_cxFreeze
    build_patchelf
    echo "----------------------------------------"

    echo "AIX system prerequisites installation finished successfully."
}

build_cxFreeze() {
    # Install cx_Freeze from source to avoid AIX wheel issues
    echo "Building cx_Freeze from source..."

    # Check if cx_Freeze has already completed build
    if [ -d "$BUILD_DIR/cx_Freeze-8.4.1" ]; then
        # Verify that the AIX build output exists
        if [ -f "$BUILD_DIR/cx_Freeze-8.4.1/build/lib.aix-ppc64-cpython-312/cx_Freeze/bases/console-cpython-312" ]; then
            echo "cx_Freeze has already completed the build. Skipping build."
            echo "If something is wrong with cx_Freeze, please delete the $BUILD_DIR/cx_Freeze-8.4.1 directory to build again."
            return 0
        fi
    fi

    # Otherwise, proceed to download and build cx_Freeze

    # Check if cx_Freeze source tarball is already downloaded
    echo "Checking for existing cx_Freeze source tarball..."
    if [ -f "/tmp/cx_Freeze-8.4.1.tar.gz" ]; then
        echo "cx_Freeze download archive already exists. Skipping download."
    else
        # Download cx_Freeze source
        echo "Downloading cx_Freeze source..."
        wget https://github.com/marcelotduarte/cx_Freeze/archive/refs/tags/8.4.1.tar.gz -O /tmp/cx_Freeze-8.4.1.tar.gz

        # Verify download
        if [ ! -f "/tmp/cx_Freeze-8.4.1.tar.gz" ]; then
            echo "ERROR! cx_Freeze source tarball not found."
            return 1
        else
            echo "cx_Freeze source tarball downloaded successfully."
        fi
    fi

    # Check if cx_Freeze source is already extracted
    echo "Checking for existing cx_Freeze source directory..."
    if [ -d "$BUILD_DIR/cx_Freeze-8.4.1" ]; then
        echo "cx_Freeze source directory already exists. Skipping extraction."
    else
        echo "Extracting cx_Freeze source..."
        gunzip -c /tmp/cx_Freeze-8.4.1.tar.gz | tar -xvf -

        # Verify extraction
        if [ ! -d "cx_Freeze-8.4.1" ]; then
            echo "ERROR! cx_Freeze source directory not found after extraction."
            return 1
        else
            echo "cx_Freeze source extracted successfully."
        fi
    fi

    # Change to cx_Freeze source directory
    echo "Changing to cx_Freeze source directory..."
    cd cx_Freeze-8.4.1

    # Copy cx_Freeze AIX setup patch
    echo "Applying AIX-specific setup patch for cx_Freeze..."
    cp -f "$BUILD_DIR/aix/setup_cxFreeze_aix.py" "$BUILD_DIR/cx_Freeze-8.4.1/setup.py"
    
    # Build cx_Freeze, we should be in the venv
    echo "Building cx_Freeze with AIX patch..."
    $PYTHONBIN setup.py build

    # Return to original directory
    cd ..

    echo "cx_Freeze build completed successfully."
}

build_patchelf() {
    echo "Building and installing patchelf from source..."

    # Check if patchelf is already installed
    if command -v /usr/local/bin/patchelf >/dev/null 2>&1; then
        echo "patchelf is already installed. Skipping build."
        return 0
    fi

    # Otherwise, proceed to download and build patchelf

    # Check if patchelf source tarball is already downloaded
    echo "Checking for existing patchelf source tarball..."
    if [ -f "/tmp/patchelf-0.18.0.tar.gz" ]; then
        echo "patchelf download archive already exists. Skipping download."
    else
        # Download patchelf source
        echo "Downloading patchelf source..."
        wget https://github.com/NixOS/patchelf/releases/download/0.18.0/patchelf-0.18.0.tar.gz -O /tmp/patchelf-0.18.0.tar.gz

        # Verify download
        if [ ! -f "/tmp/patchelf-0.18.0.tar.gz" ]; then
            echo "ERROR! patchelf source tarball not found."
            return 1
        else
            echo "patchelf source tarball downloaded."
        fi
    fi

    # Check if patchelf source is already extracted
    echo "Checking for existing patchelf source directory..."
    if [ -d "$BUILD_DIR/patchelf-0.18.0" ]; then
        echo "patchelf source directory already exists. Skipping extraction."
    else
        echo "Extracting patchelf source..."
        gunzip -c /tmp/patchelf-0.18.0.tar.gz | tar -xvf -

        if [ ! -d "patchelf-0.18.0" ]; then
            echo "ERROR! patchelf source directory not found after extraction."
            return 1
        else
            echo "patchelf source directory found."
        fi
    fi

    # Change to patchelf source directory
    echo "Changing to patchelf source directory..."
    cd patchelf-0.18.0

    echo "Configuring patchelf..."
    ./configure --prefix=/usr/local

    # Compile and install patchelf
    echo "Compiling patchelf..."
    make
    echo "Installing patchelf to /usr/local/bin..."
    make install

    # Verify installation
    if command -v /usr/local/bin/patchelf >/dev/null 2>&1; then
        echo "patchelf installed successfully."
    else
        echo "ERROR! patchelf installation failed."
        return 1
    fi

    # Return to original directory
    cd ..

    echo "patchelf build and installation completed successfully."
}

# Execute the prerequisite installation during setup
install_prereqs

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
    
    # Use pip to install cx_Freeze into the environment
    echo "***** aix/setup.sh - Installing cx_Freeze into the environment"
    $PYTHONBIN -m pip install $BUILD_DIR/cx_Freeze-8.4.1
fi
