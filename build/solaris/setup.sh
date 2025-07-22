#!/bin/bash

# Source version configuration
BUILD_DIR_FOR_VERSION=$(dirname "$(dirname "$0")")
source "$BUILD_DIR_FOR_VERSION/version_config.sh"

# Globals - Use the version from version_config.sh
PYTHONTAR="Python-$PYTHONVER"
PYTHONBIN="/opt/csw/bin/python3"

# Check if we can detect Python 3.9+ with pkg-config first
if command -v pkg-config >/dev/null 2>&1; then
    if pkg-config --exists python3; then
        PYTHONBIN=$(pkg-config --variable=exec_prefix python3)/bin/python3
    fi
fi

# Fallback to common Python locations on Solaris
if [ ! -x "$PYTHONBIN" ]; then
    for py_path in /opt/csw/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
        if [ -x "$py_path" ]; then
            PYTHONBIN="$py_path"
            break
        fi
    done
fi

# Check version of Solaris
SOLARIS_VER=$(uname -r | cut -d. -f2)
ARCH=$(arch)

update_py_packages() {
    # Update pip and install required packages for Solaris 11+
    if [ "$SOLARIS_VER" -ge 11 ]; then
        echo "Installing Python packages for Solaris 11..."
        $PYTHONBIN -m pip install --upgrade pip
        $PYTHONBIN -m pip install -r $BUILD_DIR/resources/require.txt --upgrade
    else
        echo "ERROR: Solaris 10 and older are not supported."
        echo "Please upgrade to Solaris 11 or later."
        exit 1
    fi
}

install_prereqs() {

    echo "Installing prerequisites for Solaris..."

    # --------------------------
    #  INSTALL SYSTEM REQUIREMENTS
    # --------------------------

    # Check if we're on Solaris 11 or later
    if [ "$SOLARIS_VER" -lt 11 ]; then
        echo "ERROR: Solaris 10 and older are not supported."
        echo "Please upgrade to Solaris 11 or later."
        exit 1
    fi

    # Install build essentials and dependencies
    echo "Installing system packages..."
    if command -v pkg >/dev/null 2>&1; then
        # Use pkg (Solaris 11+ package manager)
        pkg install --accept \
            developer/gcc \
            library/libffi \
            library/zlib \
            library/security/openssl \
            runtime/python-39 \
            library/python/pip-39 \
            || {
                echo "Failed to install system packages with pkg"
                echo "Falling back to alternative installation methods..."
            }
    fi

    # --------------------------
    #  INSTALL OPENCSW PACKAGES (fallback)
    # --------------------------

    echo "Setting up OpenCSW package manager..."
    if [ ! -f /opt/csw/bin/pkgutil ]; then
        echo "Installing OpenCSW..."
        pkgadd -d http://get.opencsw.org/now
        /opt/csw/bin/pkgutil -U
    fi

    # Install Python and dependencies via OpenCSW
    echo "Installing Python 3.9 via OpenCSW..."
    /opt/csw/bin/pkgutil -y -i python39 python39_dev py_pip

    # Update PATH to include CSW binaries
    export PATH=/opt/csw/bin:$PATH

    # Make sure we have the right Python
    if [ ! -x "/opt/csw/bin/python3.9" ] && [ ! -x "/opt/csw/bin/python3" ]; then
        echo "ERROR: Could not install Python 3.9"
        echo "Available Python installations:"
        find /opt/csw/bin /usr/bin /usr/local/bin -name "python*" 2>/dev/null || true
        exit 1
    fi

    # Update PATH and library paths for Solaris
    export PATH=/opt/csw/bin:/opt/csw/sbin:$PATH
    export LD_LIBRARY_PATH=/opt/csw/lib:$LD_LIBRARY_PATH
    export PKG_CONFIG_PATH=/opt/csw/lib/pkgconfig:$PKG_CONFIG_PATH

    # Update PYTHONBIN to the actual installed location
    if [ -x "/opt/csw/bin/python3.9" ]; then
        PYTHONBIN="/opt/csw/bin/python3.9"
    elif [ -x "/opt/csw/bin/python3" ]; then
        PYTHONBIN="/opt/csw/bin/python3"
    fi

    echo "Using Python: $PYTHONBIN"
    $PYTHONBIN --version

    # Export PYTHONBIN for use by the main build script
    export PYTHONBIN

    # --------------------------
    #  SETUP USER/GROUP
    # --------------------------

    echo "Setting up nagios user and group..."
    # Create nagios group if it doesn't exist
    if ! getent group nagios >/dev/null 2>&1; then
        groupadd nagios
    fi

    # Create nagios user if it doesn't exist
    if ! getent passwd nagios >/dev/null 2>&1; then
        useradd -g nagios -d /usr/local/ncpa -s /bin/false nagios
    fi

    # --------------------------
    #  INSTALL PYTHON PACKAGES
    # --------------------------

    echo "Installing Python packages..."
    update_py_packages

}
