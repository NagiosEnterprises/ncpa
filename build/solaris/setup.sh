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
        
        # Check if we have a working Python
        if [ -z "$PYTHONBIN" ] || [ ! -x "$PYTHONBIN" ]; then
            echo "ERROR: No Python binary available"
            return 1
        fi
        
        echo "Using Python: $PYTHONBIN ($($PYTHONBIN --version 2>&1))"
        
        # Check if pip is available
        if ! $PYTHONBIN -m pip --version >/dev/null 2>&1; then
            echo "pip not available, attempting to install..."
            # Try to install pip using get-pip.py
            if command -v wget >/dev/null 2>&1; then
                wget -O /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
            elif command -v curl >/dev/null 2>&1; then
                curl -k -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
            else
                echo "ERROR: Neither wget nor curl available to download pip"
                return 1
            fi
            
            if [ -f /tmp/get-pip.py ]; then
                $PYTHONBIN /tmp/get-pip.py --user
                rm -f /tmp/get-pip.py
            fi
        fi
        
        # Try to upgrade pip first
        echo "Upgrading pip..."
        $PYTHONBIN -m pip install --upgrade pip --user || {
            echo "WARNING: Could not upgrade pip, continuing with existing version"
        }
        
        # Install required packages
        echo "Installing required Python packages..."
        if [ -f "$BUILD_DIR/resources/require.txt" ]; then
            $PYTHONBIN -m pip install -r "$BUILD_DIR/resources/require.txt" --upgrade --user || {
                echo "ERROR: Failed to install required packages"
                echo "Contents of require.txt:"
                cat "$BUILD_DIR/resources/require.txt"
                return 1
            }
        else
            echo "WARNING: require.txt not found at $BUILD_DIR/resources/require.txt"
            echo "Installing packages individually..."
            for pkg in cx_Freeze psutil requests Jinja2 flask werkzeug pyOpenSSL cryptography gevent cffi; do
                echo "Installing $pkg..."
                $PYTHONBIN -m pip install "$pkg" --user || echo "WARNING: Failed to install $pkg"
            done
        fi
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

    # Function to check if a package is available in CSW
    check_csw_package() {
        local pkg="$1"
        if /opt/csw/bin/pkgutil -a | grep -q "^$pkg "; then
            return 0
        else
            return 1
        fi
    }

    # Install build essentials and dependencies
    echo "Installing system packages..."
    if command -v pkg >/dev/null 2>&1; then
        # Use pkg (Solaris 11+ package manager) - try Python 3.9 first, fallback to 3.7/3.8
        echo "Attempting to install Python via pkg..."
        for py_ver in runtime/python-39 runtime/python-38 runtime/python-37; do
            if pkg list "$py_ver" >/dev/null 2>&1; then
                echo "Installing $py_ver..."
                pkg install --accept \
                    developer/gcc \
                    library/libffi \
                    library/zlib \
                    library/security/openssl \
                    "$py_ver" \
                    && break
            fi
        done
    fi

    # --------------------------
    #  INSTALL OPENCSW PACKAGES (fallback)
    # --------------------------

    echo "Setting up OpenCSW package manager..."
    if [ ! -f /opt/csw/bin/pkgutil ]; then
        echo "Installing OpenCSW..."
        if ! pkgadd -d http://get.opencsw.org/now; then
            echo "ERROR: Failed to install OpenCSW"
            echo "Please install OpenCSW manually or use Solaris 11 pkg manager"
            exit 1
        fi
    fi
    
    # Update package catalog
    echo "Updating package catalog..."
    if ! /opt/csw/bin/pkgutil -U; then
        echo "WARNING: Failed to update package catalog"
        echo "Continuing with existing catalog..."
    fi

    # Install Python and dependencies via OpenCSW
    # Try different Python package names that are commonly available
    echo "Installing Python via OpenCSW..."
    
    # First install core build dependencies
    echo "Installing core dependencies..."
    /opt/csw/bin/pkgutil -y -i gcc4core ggettext libiconv zlib openssl libffi
    
    # Check what Python packages are available and install one
    echo "Checking available Python packages..."
    python_installed=false
    for py_pkg in python3 python39 python38 python37 python36; do
        if check_csw_package "$py_pkg"; then
            echo "Package $py_pkg is available, installing..."
            if /opt/csw/bin/pkgutil -y -i "$py_pkg"; then
                echo "Successfully installed $py_pkg"
                python_installed=true
                break
            fi
        else
            echo "Package $py_pkg is not available in catalog"
        fi
    done

    if [ "$python_installed" = false ]; then
        echo "WARNING: Could not install Python via CSW packages"
        echo "Available packages in catalog:"
        /opt/csw/bin/pkgutil -a | grep python || echo "No Python packages found"
    fi

    # Install pip separately if available
    if check_csw_package "py_pip"; then
        /opt/csw/bin/pkgutil -y -i py_pip
    else
        echo "pip not available via CSW, will install manually later"
    fi

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
    export PATH=/opt/csw/bin:/opt/csw/sbin:/usr/bin:/usr/local/bin:$PATH
    export LD_LIBRARY_PATH=/opt/csw/lib:/usr/lib:$LD_LIBRARY_PATH
    export PKG_CONFIG_PATH=/opt/csw/lib/pkgconfig:/usr/lib/pkgconfig:$PKG_CONFIG_PATH

    # Update PYTHONBIN to the actual installed location
    echo "Detecting Python installation..."
    for py_path in \
        "/opt/csw/bin/python3.9" \
        "/opt/csw/bin/python3.8" \
        "/opt/csw/bin/python3.7" \
        "/opt/csw/bin/python3" \
        "/usr/bin/python3.9" \
        "/usr/bin/python3.8" \
        "/usr/bin/python3.7" \
        "/usr/bin/python3" \
        "/usr/local/bin/python3"; do
        
        if [ -x "$py_path" ]; then
            PYTHONBIN="$py_path"
            echo "Found Python at: $PYTHONBIN"
            break
        fi
    done

    if [ -z "$PYTHONBIN" ] || [ ! -x "$PYTHONBIN" ]; then
        echo "ERROR: Could not find a suitable Python 3 installation"
        echo "Available Python installations:"
        find /opt/csw/bin /usr/bin /usr/local/bin -name "python*" -executable 2>/dev/null || true
        exit 1
    fi

    echo "Using Python: $PYTHONBIN"
    $PYTHONBIN --version

    # Install pip if not available
    if ! $PYTHONBIN -m pip --version >/dev/null 2>&1; then
        echo "Installing pip..."
        # Download and install pip
        curl -k https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
        $PYTHONBIN /tmp/get-pip.py --user
        rm -f /tmp/get-pip.py
    fi

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
