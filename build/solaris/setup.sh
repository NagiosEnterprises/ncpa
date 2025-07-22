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
        solaris_requirements="$BUILD_DIR/resources/require-solaris.txt"
        standard_requirements="$BUILD_DIR/resources/require.txt"
        
        if [ -f "$solaris_requirements" ]; then
            echo "Found Solaris-specific require-solaris.txt, installing packages..."
            $PYTHONBIN -m pip install -r "$solaris_requirements" --upgrade --user || {
                echo "WARNING: Some packages failed to install, continuing with individual installation"
                # Try installing packages individually for better error handling
                while IFS= read -r pkg; do
                    if [ -n "$pkg" ] && [ "${pkg#\#}" = "$pkg" ]; then  # Skip empty lines and comments
                        echo "Installing $pkg..."
                        if [ "$pkg" = "cryptography" ] || [ "$pkg" = "cffi" ]; then
                            $PYTHONBIN -m pip install "$pkg" --user || echo "WARNING: Failed to install $pkg (not critical for basic SSL support)"
                        else
                            $PYTHONBIN -m pip install "$pkg" --user || echo "WARNING: Failed to install $pkg"
                        fi
                    fi
                done < "$solaris_requirements"
            }
        elif [ -f "$standard_requirements" ]; then
            echo "Found standard require.txt, filtering out pyOpenSSL for Solaris..."
            # Create a temporary requirements file without pyOpenSSL
            temp_req="/tmp/require-solaris-temp.txt"
            grep -v "^pyOpenSSL" "$standard_requirements" > "$temp_req"
            
            $PYTHONBIN -m pip install -r "$temp_req" --upgrade --user || {
                echo "WARNING: Some packages failed to install, continuing with individual installation"
                # Try installing packages individually for better error handling
                while IFS= read -r pkg; do
                    if [ -n "$pkg" ] && [ "${pkg#\#}" = "$pkg" ]; then  # Skip empty lines and comments
                        echo "Installing $pkg..."
                        if [ "$pkg" = "cryptography" ] || [ "$pkg" = "cffi" ]; then
                            $PYTHONBIN -m pip install "$pkg" --user || echo "WARNING: Failed to install $pkg (not critical for basic SSL support)"
                        else
                            $PYTHONBIN -m pip install "$pkg" --user || echo "WARNING: Failed to install $pkg"
                        fi
                    fi
                done < "$temp_req"
            }
            rm -f "$temp_req"
        else
            echo "WARNING: require.txt not found at $BUILD_DIR/resources/require.txt"
            echo "Installing packages individually..."
            # Note: Skipping pyOpenSSL since we'll use Python's built-in ssl module
            for pkg in cx_Freeze psutil requests Jinja2 flask werkzeug cryptography gevent cffi; do
                echo "Installing $pkg..."
                if [ "$pkg" = "cryptography" ] || [ "$pkg" = "cffi" ]; then
                    $PYTHONBIN -m pip install "$pkg" --user || echo "WARNING: Failed to install $pkg (not critical for basic SSL support)"
                else
                    $PYTHONBIN -m pip install "$pkg" --user || echo "WARNING: Failed to install $pkg"
                fi
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

    # Check for available package managers
    echo "Checking available package managers..."
    if command -v pkg >/dev/null 2>&1; then
        echo "✓ IPS (Image Packaging System) available"
    else
        echo "✗ IPS (Image Packaging System) not available"
    fi
    
    if [ -f /opt/csw/bin/pkgutil ]; then
        echo "✓ OpenCSW package manager available"
    else
        echo "✗ OpenCSW not installed - attempting to install..."
        if command -v pkgadd >/dev/null 2>&1; then
            pkgadd -d http://get.opencsw.org/now
            /opt/csw/bin/pkgutil -U
        else
            echo "WARNING: Cannot install OpenCSW - pkgadd not available"
        fi
    fi

    # Run package availability check first
    if [ -f "$BUILD_DIR/solaris/check_packages.sh" ]; then
        echo "Running pre-flight package check..."
        if "$BUILD_DIR/solaris/check_packages.sh"; then
            echo "Package check passed, proceeding with installation..."
        else
            echo "WARNING: Package check found missing dependencies"
            echo "Continuing anyway, but some packages may fail to install..."
        fi
    fi

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

    # Function to check if a package is available in IPS (native Solaris 11)
    check_ips_package() {
        local pkg="$1"
        if command -v pkg >/dev/null 2>&1; then
            if pkg list -a "$pkg" >/dev/null 2>&1; then
                return 0
            fi
        fi
        return 1
    }

    # Function to safely install a package if available
    safe_install_package() {
        local pkg="$1"
        local description="$2"
        echo "Attempting to install $pkg ($description)..."
        
        # First try CSW if package is available there
        if check_csw_package "$pkg"; then
            if /opt/csw/bin/pkgutil -y -i "$pkg"; then
                echo "Successfully installed $pkg via CSW"
                return 0
            else
                echo "Failed to install $pkg via CSW"
            fi
        else
            echo "Package $pkg not available in CSW catalog"
        fi
        
        # If CSW failed or package not available, try IPS (native Solaris 11)
        echo "Trying native Solaris IPS package manager..."
        if check_ips_package "$pkg"; then
            if sudo pkg install "$pkg"; then
                echo "Successfully installed $pkg via IPS"
                return 0
            else
                echo "Failed to install $pkg via IPS"
            fi
        else
            echo "Package $pkg not available in IPS catalog"
        fi
        
        return 1
    }

    # Function to install a package with fallbacks
    install_with_fallbacks() {
        local description="$1"
        shift
        local packages=("$@")
        
        echo "Installing $description..."
        for pkg in "${packages[@]}"; do
            if safe_install_package "$pkg" "$description"; then
                return 0
            fi
        done
        
        echo "WARNING: Could not install $description - tried: ${packages[*]}"
        
        # Special handling for critical packages
        if [[ "$description" == *"zlib"* ]]; then
            echo "CRITICAL: zlib is required for Python. Checking system libraries..."
            # Check if zlib is already available on the system
            if [ -f "/usr/lib/libz.so" ] || [ -f "/lib/libz.so" ] || [ -f "/usr/local/lib/libz.so" ]; then
                echo "Found system zlib library, continuing..."
                return 0
            else
                echo "ERROR: No zlib library found on system"
                echo "Available library paths:"
                find /usr/lib /lib /usr/local/lib -name "*libz*" 2>/dev/null || echo "No zlib libraries found"
                return 1
            fi
        fi
        
        return 1
    }

    # Function to install Python packages via OpenCSW with correct naming
    install_python_packages_csw() {
        echo "Installing Python packages via OpenCSW..."
        
        # Map of Python package names to OpenCSW equivalents
        declare -A py_pkg_map=(
            ["openssl"]="py_openssl"
            ["cryptography"]="py_cryptography" 
            ["cffi"]="py_cffi"
            ["requests"]="py_requests"
            ["jinja2"]="py_jinja2"
            ["flask"]="py_flask"
            ["psutil"]="py_psutil"
        )
        
        # Try to install Python packages via OpenCSW first
        for req_pkg in openssl cryptography cffi requests jinja2 flask psutil; do
            csw_pkg="${py_pkg_map[$req_pkg]}"
            if [ -n "$csw_pkg" ]; then
                safe_install_package "$csw_pkg" "Python $req_pkg"
            fi
        done
    }

    # Install build essentials and dependencies
    echo "Installing system packages..."
    
    # First try the native Solaris 11 pkg manager for core dependencies
    if command -v pkg >/dev/null 2>&1; then
        echo "Attempting to install core dependencies via native pkg manager..."
        
        # Try to install zlib through pkg first
        if pkg list library/zlib >/dev/null 2>&1; then
            echo "Installing zlib via pkg..."
            pkg install --accept library/zlib || echo "Failed to install zlib via pkg"
        fi
        
        # Try to install other core libraries (skip OpenSSL, use Python's built-in SSL)
        for pkg_name in library/libffi developer/gcc; do
            if pkg list "$pkg_name" >/dev/null 2>&1; then
                echo "Installing $pkg_name via pkg..."
                pkg install --accept "$pkg_name" || echo "Failed to install $pkg_name via pkg"
            fi
        done
        
        # Try Python installation via pkg
        for py_ver in runtime/python-39 runtime/python-38 runtime/python-37; do
            if pkg list "$py_ver" >/dev/null 2>&1; then
                echo "Installing $py_ver..."
                pkg install --accept "$py_ver" && break
            fi
        done
    else
        echo "Native pkg manager not available, will use OpenCSW only"
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

    # Debug: Show some information about available packages
    echo "Checking catalog status..."
    echo "Total packages available: $(/opt/csw/bin/pkgutil -a | wc -l)"
    echo "Sample of available packages:"
    /opt/csw/bin/pkgutil -a | head -5
    
    # Debug: Check for zlib-related packages
    echo "Checking for zlib-related packages in catalog..."
    /opt/csw/bin/pkgutil -a | grep -i zlib | head -10 || echo "No zlib packages found"
    
    # Debug: Check for compression-related packages
    echo "Checking for compression-related packages..."
    /opt/csw/bin/pkgutil -a | grep -E "(compress|zip|gz)" | head -5 || echo "No compression packages found"

    # Install Python and dependencies via OpenCSW
    # Try different Python package names that are commonly available
    echo "Installing dependencies via OpenCSW..."
    
    # First check if critical libraries are already available
    echo "Checking for existing system libraries..."
    
    # Check for zlib
    zlib_available=false
    for zlib_path in /usr/lib/libz.so* /lib/libz.so* /usr/local/lib/libz.so* /opt/csw/lib/libz.so*; do
        if [ -f "$zlib_path" ]; then
            echo "Found existing zlib: $zlib_path"
            zlib_available=true
            break
        fi
    done
    
    # Check for zlib headers
    zlib_headers=false
    for header_path in /usr/include/zlib.h /usr/local/include/zlib.h /opt/csw/include/zlib.h; do
        if [ -f "$header_path" ]; then
            echo "Found zlib headers: $header_path"
            zlib_headers=true
            break
        fi
    done
    
    # Install core build dependencies with fallbacks
    echo "Installing core build dependencies..."
    install_with_fallbacks "GCC compiler" gcc4core gcc4g++ gcc gcc4 gccdev
    install_with_fallbacks "GNU gettext" ggettext gettext
    
    # Handle zlib specially
    if [ "$zlib_available" = true ]; then
        echo "Skipping zlib installation - already available on system"
    else
        echo "Attempting to install zlib..."
        if ! install_with_fallbacks "zlib library" zlib libz zlib1 libzlib zlib_dev libz_dev; then
            echo "WARNING: Could not install zlib via packages"
            echo "Checking if zlib can be found anyway..."
            
            # Run the zlib detection script if available
            if [ -f "$BUILD_DIR/solaris/detect_zlib.sh" ]; then
                echo "Running zlib detection..."
                "$BUILD_DIR/solaris/detect_zlib.sh"
            fi
            
            # Continue anyway - Python might have its own zlib or find it elsewhere
            echo "Continuing build despite zlib package installation failure..."
        fi
    fi
    
    # Install system OpenSSL (for system libraries) - SKIPPED
    # We rely on Python's built-in SSL support instead of system OpenSSL packages
    echo "Skipping system OpenSSL installation - using Python's built-in SSL support"
    
    install_with_fallbacks "libffi library" libffi ffi libffi_dev ffi_dev
    
    # Try to install additional useful packages
    echo "Installing additional development packages..."
    safe_install_package "gcc4g++" "GCC C++ compiler"
    safe_install_package "pkgconfig" "pkg-config utility"
    
    # Install make - try multiple package names for different package managers
    echo "Installing GNU make..."
    if ! safe_install_package "make" "GNU make"; then
        # Try IPS package names for Solaris 11
        echo "Trying Solaris 11 IPS packages..."
        if check_ips_package "developer/build/gnu-make"; then
            if sudo pkg install developer/build/gnu-make; then
                echo "Successfully installed GNU make via IPS (developer/build/gnu-make)"
            else
                echo "Failed to install GNU make via IPS"
            fi
        elif check_ips_package "developer/build/make"; then
            if sudo pkg install developer/build/make; then
                echo "Successfully installed make via IPS (developer/build/make)"
            else
                echo "Failed to install make via IPS"
            fi
        elif check_ips_package "system/header"; then
            # Install system development headers which includes make utilities
            if sudo pkg install system/header; then
                echo "Successfully installed system development tools (includes make)"
            else
                echo "Failed to install system development tools"
            fi
        elif check_ips_package "build-essential"; then
            # Some Solaris distributions have a build-essential package
            if sudo pkg install build-essential; then
                echo "Successfully installed build-essential package"
            else
                echo "Failed to install build-essential"
            fi
        else
            echo "WARNING: Could not install GNU make via IPS. Trying gmake as fallback..."
            safe_install_package "gmake" "GNU make alternative"
        fi
    fi
    
    safe_install_package "bzip2" "bzip2 compression"
    safe_install_package "libbz2_dev" "bzip2 development"
    safe_install_package "readline" "readline library"
    safe_install_package "ncurses" "ncurses library"
    
    # Install Python-specific packages (skip OpenSSL - use Python's built-in SSL)
    echo "Installing Python-specific packages..."
    echo "Skipping py_openssl - using Python's built-in SSL support"
    safe_install_package "py_cryptography" "Python cryptography"
    safe_install_package "py_cffi" "Python CFFI"
    
    # Install additional Python packages if available
    install_python_packages_csw
    
    # Check what Python packages are available and install one
    echo "Installing Python..."
    python_installed=false
    if install_with_fallbacks "Python interpreter" python3 python39 python38 python37 python36; then
        python_installed=true
    fi

    if [ "$python_installed" = false ]; then
        echo "WARNING: Could not install Python via CSW packages"
        echo "Listing available Python-related packages:"
        /opt/csw/bin/pkgutil -a | grep -i python | head -10 || echo "No Python packages found"
    fi

    # Install pip separately if available
    echo "Installing pip..."
    if ! install_with_fallbacks "Python pip" py_pip python_pip pip; then
        echo "pip not available via CSW, will install manually later"
    fi

    # Update PATH to include CSW binaries and other common Solaris locations
    export PATH=/opt/csw/bin:/opt/csw/sbin:/usr/sfw/bin:/usr/ccs/bin:/usr/bin:/usr/local/bin:$PATH

    # Make sure we have the right Python
    if [ ! -x "/opt/csw/bin/python3.9" ] && [ ! -x "/opt/csw/bin/python3" ]; then
        echo "ERROR: Could not install Python 3.9"
        echo "Available Python installations:"
        find /opt/csw/bin /usr/bin /usr/local/bin -name "python*" 2>/dev/null || true
        exit 1
    fi

    # Update PATH and library paths for Solaris
    export PATH=/opt/csw/bin:/opt/csw/sbin:/usr/sfw/bin:/usr/ccs/bin:/usr/bin:/usr/local/bin:$PATH
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
    #  VERIFY CRITICAL TOOLS
    # --------------------------

    echo "Verifying critical build tools..."
    
    # Check for make or gmake
    if command -v make >/dev/null 2>&1; then
        echo "✓ make available: $(which make)"
        make --version | head -1 || echo "make version check failed"
    elif command -v gmake >/dev/null 2>&1; then
        echo "✓ gmake available: $(which gmake)"
        gmake --version | head -1 || echo "gmake version check failed"
        # Create a make symlink if it doesn't exist
        if [ ! -e /opt/csw/bin/make ] && [ -w /opt/csw/bin ]; then
            ln -s "$(which gmake)" /opt/csw/bin/make
            echo "Created make symlink to gmake"
        fi
    else
        echo "✗ Neither make nor gmake found"
        echo "Running diagnostic script for troubleshooting..."
        if [ -f "$BUILD_DIR/solaris/debug_make_packages.sh" ]; then
            "$BUILD_DIR/solaris/debug_make_packages.sh"
        else
            echo "Available in PATH:"
            echo "$PATH" | tr ':' '\n' | while read -r dir; do
                [ -d "$dir" ] && ls -la "$dir"/*make* 2>/dev/null || true
            done
        fi
        echo "WARNING: Build may fail without make"
    fi
    
    # Check for gcc
    if command -v gcc >/dev/null 2>&1; then
        echo "✓ gcc available: $(which gcc)"
    else
        echo "✗ gcc not found - this may cause build issues"
    fi

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
