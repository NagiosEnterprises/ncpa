#!/bin/bash

# Source version configuration
BUILD_DIR_FOR_VERSION=$(dirname "$(dirname "$0")")
if [ ! -f "$BUILD_DIR_FOR_VERSION/version_config.sh" ]; then
    echo "ERROR: Cannot find version_config.sh at $BUILD_DIR_FOR_VERSION/version_config.sh"
    exit 1
fi

echo "Loading version configuration from: $BUILD_DIR_FOR_VERSION/version_config.sh"
source "$BUILD_DIR_FOR_VERSION/version_config.sh"

# Validate that required variables are set
if [ -z "$PYTHONVER" ] || [ -z "$PYTHON_MAJOR_MINOR" ]; then
    echo "ERROR: Required version variables not set. Check version_config.sh"
    echo "PYTHONVER: '$PYTHONVER'"
    echo "PYTHON_MAJOR_MINOR: '$PYTHON_MAJOR_MINOR'"
    exit 1
fi

# Globals - Use the version from version_config.sh
PYTHONTAR="Python-$PYTHONVER"
PYTHONBIN=""
PREFERRED_PYTHON_VERSION="$PYTHON_MAJOR_MINOR"  # Use version from config (e.g., "3.13")
NO_INTERACTION="${NO_INTERACTION:-0}"  # Default to interactive mode if not set

# Build directory for referencing other scripts
BUILD_DIR="${BUILD_DIR_FOR_VERSION}"

# Debug output for version configuration
echo "=== Version Configuration ==="
echo "PYTHONVER: $PYTHONVER"
echo "PYTHON_MAJOR_MINOR: $PYTHON_MAJOR_MINOR"
echo "PREFERRED_PYTHON_VERSION: $PREFERRED_PYTHON_VERSION"
echo "SSLVER: $SSLVER"
echo "ZLIBVER: $ZLIBVER"
echo "================================"
echo ""

# Check if we can detect the configured Python version first
if command -v pkg-config >/dev/null 2>&1; then
    if pkg-config --exists python3; then
        potential_pythonbin=$(pkg-config --variable=exec_prefix python3)/bin/python3
        if [ -x "$potential_pythonbin" ]; then
            # Check if this Python matches our preferred version
            py_version=$($potential_pythonbin --version 2>&1 | sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -1)
            if [ -n "$py_version" ]; then
                major=$(echo "$py_version" | cut -d. -f1)
                minor=$(echo "$py_version" | cut -d. -f2)
                if [ "$py_version" = "$PREFERRED_PYTHON_VERSION" ]; then
                    echo "Found exact match for preferred Python $PREFERRED_PYTHON_VERSION via pkg-config"
                    PYTHONBIN="$potential_pythonbin"
                elif [ "$major" -gt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -ge 6 ]); then
                    echo "Found compatible Python $py_version via pkg-config (not preferred $PREFERRED_PYTHON_VERSION)"
                    PYTHONBIN="$potential_pythonbin"
                fi
            fi
        fi
    fi
fi

# Fallback to common Python locations on Solaris (prefer configured version, then IPS over OpenCSW)
if [ -z "$PYTHONBIN" ] || [ ! -x "$PYTHONBIN" ]; then
    echo "Searching for Python $PREFERRED_PYTHON_VERSION or compatible versions..."
    
    # First, explicitly check for the configured Python version in all common locations
    preferred_paths=(
        "/usr/bin/python$PREFERRED_PYTHON_VERSION"
        "/usr/local/bin/python$PREFERRED_PYTHON_VERSION" 
        "/opt/csw/bin/python$PREFERRED_PYTHON_VERSION"
        "/usr/bin/python${PYTHON_MAJOR}"
        "/usr/local/bin/python${PYTHON_MAJOR}"
        "/opt/csw/bin/python${PYTHON_MAJOR}"
    )
    
    for py_path in "${preferred_paths[@]}"; do
        if [ -x "$py_path" ]; then
            # Check if this Python matches our preferred version
            py_version=$($py_path --version 2>&1 | sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -1)
            if [ -n "$py_version" ]; then
                if [ "$py_version" = "$PREFERRED_PYTHON_VERSION" ]; then
                    PYTHONBIN="$py_path"
                    echo "Found exact match for preferred Python $PREFERRED_PYTHON_VERSION: $PYTHONBIN"
                    break
                fi
            fi
        fi
    done
    
    # If no exact match found, fallback to other compatible versions
    if [ -z "$PYTHONBIN" ]; then
        echo "No exact match for Python $PREFERRED_PYTHON_VERSION found, checking compatible versions..."
        fallback_paths=(
            "/usr/bin/python3.13" "/usr/bin/python3.12" "/usr/bin/python3.11" 
            "/usr/bin/python3.10" "/usr/bin/python3.9" "/usr/bin/python3.8" 
            "/usr/bin/python3" 
            "/usr/local/bin/python3.13" "/usr/local/bin/python3.12" "/usr/local/bin/python3.11"
            "/usr/local/bin/python3.10" "/usr/local/bin/python3.9" "/usr/local/bin/python3"
            "/opt/csw/bin/python3.13" "/opt/csw/bin/python3.12" "/opt/csw/bin/python3.11"
            "/opt/csw/bin/python3.10" "/opt/csw/bin/python3.9" "/opt/csw/bin/python3"
        )
        
        for py_path in "${fallback_paths[@]}"; do
            if [ -x "$py_path" ]; then
                # Check if this Python is 3.6 or newer
                py_version=$($py_path --version 2>&1 | sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -1)
                if [ -n "$py_version" ]; then
                    major=$(echo "$py_version" | cut -d. -f1)
                    minor=$(echo "$py_version" | cut -d. -f2)
                    if [ "$major" -gt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -ge 6 ]); then
                        PYTHONBIN="$py_path"
                        echo "Found compatible Python $py_version: $PYTHONBIN"
                        break
                    fi
                fi
            fi
        done
    fi
fi

# If still no suitable Python found, set to default (will be handled later)
if [ -z "$PYTHONBIN" ]; then
    PYTHONBIN="/usr/bin/python3"
fi

# Check version of Solaris
SOLARIS_VER=$(uname -r | cut -d. -f2)
ARCH=$(arch)

# Override with configured Python version if available (preferred version)
echo "Checking for configured Python version ($PREFERRED_PYTHON_VERSION)..."
override_paths=(
    "/usr/bin/python$PREFERRED_PYTHON_VERSION"
    "/usr/local/bin/python$PREFERRED_PYTHON_VERSION"
    "/opt/csw/bin/python$PREFERRED_PYTHON_VERSION"
    "/usr/bin/python${PYTHON_MAJOR}"
    "/usr/local/bin/python${PYTHON_MAJOR}"
    "/opt/csw/bin/python${PYTHON_MAJOR}"
)

for preferred_py in "${override_paths[@]}"; do
    if [ -x "$preferred_py" ]; then
        py_version=$($preferred_py --version 2>&1 | sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -1)
        if [ -n "$py_version" ]; then
            if [ "$py_version" = "$PREFERRED_PYTHON_VERSION" ]; then
                echo "Overriding with configured Python $PREFERRED_PYTHON_VERSION: $preferred_py"
                PYTHONBIN="$preferred_py"
                break
            elif [ "${py_version%.*}" = "${PREFERRED_PYTHON_VERSION%.*}" ]; then
                # Same major.minor, different patch version
                echo "Found compatible Python $py_version (close to preferred $PREFERRED_PYTHON_VERSION): $preferred_py"
                PYTHONBIN="$preferred_py"
                break
            fi
        fi
    fi
done

# Early Python detection output
echo "Early Python detection:"
echo "  PYTHONBIN: $PYTHONBIN"
if [ -x "$PYTHONBIN" ]; then
    echo "  Version: $($PYTHONBIN --version 2>&1)"
    # Export PYTHONBIN early so it's available to the build process
    export PYTHONBIN
else
    echo "  ERROR: Python binary not executable or not found"
fi
echo ""

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

    # Function to check if a library is available on the system
    check_system_library() {
        local lib_name="$1"
        local lib_description="$2"
        echo "Checking for $lib_description..."
        
        # Common library paths on Solaris
        local lib_paths=(
            "/usr/lib/lib${lib_name}.so*"
            "/lib/lib${lib_name}.so*" 
            "/usr/local/lib/lib${lib_name}.so*"
            "/opt/csw/lib/lib${lib_name}.so*"
            "/usr/sfw/lib/lib${lib_name}.so*"
        )
        
        for lib_pattern in "${lib_paths[@]}"; do
            for lib_file in $lib_pattern; do
                if [ -f "$lib_file" ]; then
                    echo "✓ Found $lib_description: $lib_file"
                    return 0
                fi
            done
        done
        
        echo "✗ $lib_description not found"
        return 1
    }

    # Function to build Python from source as a last resort
    build_python_from_source() {
        local python_version="$PYTHONVER"  # Use configured version
        local python_url="https://www.python.org/ftp/python/${python_version}/Python-${python_version}.tgz"
        local build_dir="/tmp/python-build-$$"
        
        echo "Building Python ${python_version} from source (configured version)..."
        echo "This may take 10-30 minutes depending on your system..."
        
        # Check for required tools
        for tool in gcc make wget; do
            if ! command -v $tool >/dev/null 2>&1; then
                echo "ERROR: $tool is required but not found"
                echo "Please install development tools first"
                return 1
            fi
        done
        
        # Create build directory
        mkdir -p "$build_dir"
        cd "$build_dir"
        
        # Download Python source
        echo "Downloading Python source..."
        if ! wget "$python_url"; then
            echo "ERROR: Failed to download Python source"
            return 1
        fi
        
        # Extract
        echo "Extracting Python source..."
        if ! tar -xzf "Python-${python_version}.tgz"; then
            echo "ERROR: Failed to extract Python source"
            return 1
        fi
        
        cd "Python-${python_version}"
        
        # Configure with appropriate options for Solaris
        echo "Configuring Python build..."
        ./configure \
            --prefix=/usr/local \
            --enable-shared \
            --enable-optimizations \
            --with-ssl \
            --with-ssl-default-suites=openssl \
            LDFLAGS="-L/opt/csw/lib -L/usr/lib" \
            CPPFLAGS="-I/opt/csw/include -I/usr/include" \
            PKG_CONFIG_PATH="/opt/csw/lib/pkgconfig:/usr/lib/pkgconfig" || {
            echo "ERROR: Python configure failed"
            return 1
        }
        
        # Build
        echo "Building Python (this will take a while)..."
        if ! make -j$(nproc 2>/dev/null || echo 2); then
            echo "ERROR: Python build failed"
            return 1
        fi
        
        # Install
        echo "Installing Python to /usr/local..."
        if ! sudo make install; then
            echo "ERROR: Python installation failed"
            return 1
        fi
        
        # Update library path
        echo "/usr/local/lib" | sudo tee -a /etc/ld.so.conf.d/python.conf 2>/dev/null || true
        sudo ldconfig 2>/dev/null || true
        
        # Cleanup
        cd /
        rm -rf "$build_dir"
        
        echo "✓ Python ${python_version} built and installed successfully"
        return 0
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
        
        # Try to install Python first via IPS - prefer the configured version
        echo "Installing Python via IPS (native Solaris package manager)..."
        echo "Preferred version: Python $PREFERRED_PYTHON_VERSION"
        
        # Build IPS package list with configured version first
        ips_python_packages=(
            "runtime/python-${PYTHON_MAJOR}${PYTHON_MAJOR_MINOR#*.}"  # e.g., runtime/python-313
            "runtime/python-313" "runtime/python-312" "runtime/python-311" 
            "runtime/python-310" "runtime/python-39" "runtime/python-38"
        )
        
        python_ips_installed=false
        for py_ver in "${ips_python_packages[@]}"; do
            if check_ips_package "$py_ver"; then
                echo "Installing $py_ver..."
                if sudo pkg install --accept "$py_ver"; then
                    echo "Successfully installed $py_ver"
                    python_ips_installed=true
                    # Also try to install development tools for this Python version
                    dev_pkg=$(echo "$py_ver" | sed 's/runtime/developer/')
                    if check_ips_package "$dev_pkg"; then
                        sudo pkg install --accept "$dev_pkg" || echo "Could not install $dev_pkg"
                    fi
                    break
                else
                    echo "Failed to install $py_ver"
                fi
            fi
        done
        
        if [ "$python_ips_installed" = false ]; then
            echo "No suitable Python found in IPS, will try other methods..."
        fi
        
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
    /opt/csw/bin/pkgutil -a | grep "compress\|zip\|gz" | head -5 || echo "No compression packages found"

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
    
    # Install bzip2 - try multiple package names for different package managers
    echo "Installing bzip2 compression library..."
    if ! safe_install_package "bzip2" "bzip2 compression"; then
        echo "Trying Solaris 11 IPS packages for bzip2..."
        if check_ips_package "compress/bzip2"; then
            if sudo pkg install compress/bzip2; then
                echo "Successfully installed bzip2 via IPS (compress/bzip2)"
            else
                echo "Failed to install bzip2 via IPS"
            fi
        elif check_ips_package "library/bzip2"; then
            if sudo pkg install library/bzip2; then
                echo "Successfully installed bzip2 via IPS (library/bzip2)"
            else
                echo "Failed to install bzip2 via IPS"
            fi
        else
            echo "WARNING: Could not install bzip2 via IPS"
            check_system_library "bz2" "bzip2 library"
        fi
    fi
    
    # Install bzip2 development headers
    echo "Installing bzip2 development headers..."
    if ! safe_install_package "libbz2_dev" "bzip2 development"; then
        echo "Trying Solaris 11 IPS packages for bzip2 development..."
        if check_ips_package "developer/library/bzip2"; then
            if sudo pkg install developer/library/bzip2; then
                echo "Successfully installed bzip2 development via IPS"
            else
                echo "Failed to install bzip2 development via IPS"
            fi
        else
            echo "WARNING: Could not install bzip2 development headers"
            # Check if headers are available
            for header_path in /usr/include/bzlib.h /usr/local/include/bzlib.h /opt/csw/include/bzlib.h; do
                if [ -f "$header_path" ]; then
                    echo "Found bzip2 headers: $header_path"
                    break
                fi
            done
        fi
    fi
    
    # Install readline - try multiple package names for different package managers
    echo "Installing readline library..."
    if ! safe_install_package "readline" "readline library"; then
        # Try IPS package names for Solaris 11
        echo "Trying Solaris 11 IPS packages for readline..."
        if check_ips_package "library/readline"; then
            if sudo pkg install library/readline; then
                echo "Successfully installed readline via IPS (library/readline)"
            else
                echo "Failed to install readline via IPS"
            fi
        elif check_ips_package "system/library/readline"; then
            if sudo pkg install system/library/readline; then
                echo "Successfully installed readline via IPS (system/library/readline)"
            else
                echo "Failed to install readline via IPS"
            fi
        elif check_ips_package "library/libedit"; then
            # libedit is a readline alternative
            if sudo pkg install library/libedit; then
                echo "Successfully installed libedit (readline alternative) via IPS"
            else
                echo "Failed to install libedit via IPS"
            fi
        else
            echo "WARNING: Could not install readline via IPS"
            # Check if readline is already available on the system
            for readline_path in /usr/lib/libreadline.so* /lib/libreadline.so* /usr/local/lib/libreadline.so*; do
                if [ -f "$readline_path" ]; then
                    echo "Found existing readline library: $readline_path"
                    break
                fi
            done
            echo "For more package options, run: $BUILD_DIR/solaris/check_ips_packages.sh"
        fi
    fi
    
    # Install ncurses - try multiple package names
    echo "Installing ncurses library..."
    if ! safe_install_package "ncurses" "ncurses library"; then
        echo "Trying Solaris 11 IPS packages for ncurses..."
        if check_ips_package "library/ncurses"; then
            if sudo pkg install library/ncurses; then
                echo "Successfully installed ncurses via IPS (library/ncurses)"
            else
                echo "Failed to install ncurses via IPS"
            fi
        elif check_ips_package "system/library/ncurses"; then
            if sudo pkg install system/library/ncurses; then
                echo "Successfully installed ncurses via IPS (system/library/ncurses)"
            else
                echo "Failed to install ncurses via IPS"
            fi
        else
            echo "WARNING: Could not install ncurses via IPS"
            # Check if ncurses is already available on the system
            for ncurses_path in /usr/lib/libncurses.so* /lib/libncurses.so* /usr/local/lib/libncurses.so*; do
                if [ -f "$ncurses_path" ]; then
                    echo "Found existing ncurses library: $ncurses_path"
                    break
                fi
            done
        fi
    fi
    
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

    # Update PYTHONBIN to the actual installed location (prefer configured version, then IPS over CSW)
    echo "Detecting Python installation..."
    echo "Looking for configured Python version: $PREFERRED_PYTHON_VERSION"
    
    # First, explicitly check for the configured Python version in all common locations
    preferred_detection_paths=(
        "/usr/bin/python$PREFERRED_PYTHON_VERSION"
        "/usr/local/bin/python$PREFERRED_PYTHON_VERSION"
        "/opt/csw/bin/python$PREFERRED_PYTHON_VERSION"
    )
    
    for py_path in "${preferred_detection_paths[@]}"; do
        if [ -x "$py_path" ]; then
            # Check if this Python matches our configured version
            py_version=$($py_path --version 2>&1 | sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -1)
            if [ -n "$py_version" ]; then
                if [ "$py_version" = "$PREFERRED_PYTHON_VERSION" ] || [ "${py_version%.*}" = "${PREFERRED_PYTHON_VERSION%.*}" ]; then
                    PYTHONBIN="$py_path"
                    echo "Found configured Python $py_version: $PYTHONBIN"
                    echo "✓ Python version $py_version is suitable"
                    break
                fi
            fi
        fi
    done
    
    # If no configured version found, fallback to other versions
    if [ -z "$PYTHONBIN" ]; then
        echo "Configured Python $PREFERRED_PYTHON_VERSION not found, checking fallback versions..."
        fallback_detection_paths=(
            "/usr/bin/python3.13" "/usr/bin/python3.12" "/usr/bin/python3.11"
            "/usr/bin/python3.10" "/usr/bin/python3.9" "/usr/bin/python3.8"
            "/usr/bin/python3" 
            "/opt/csw/bin/python3.9" "/opt/csw/bin/python3.8" "/opt/csw/bin/python3.7"
            "/opt/csw/bin/python3" "/usr/local/bin/python3"
        )
        
        for py_path in "${fallback_detection_paths[@]}"; do
            if [ -x "$py_path" ]; then
                PYTHONBIN="$py_path"
                echo "Found Python at: $PYTHONBIN"
                # Check Python version to ensure it's 3.6 or newer
                py_version=$($PYTHONBIN --version 2>&1 | sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -1)
                echo "Python version: $py_version"
                
                # Check if version is >= 3.6 (minimum for modern pip)
                if [ -n "$py_version" ]; then
                    major=$(echo "$py_version" | cut -d. -f1)
                    minor=$(echo "$py_version" | cut -d. -f2)
                    if [ "$major" -gt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -ge 6 ]); then
                        echo "✓ Python version $py_version is suitable"
                        break
                    else
                        echo "✗ Python version $py_version is too old (need >= 3.6)"
                        PYTHONBIN=""
                    fi
                fi
            fi
        done
    fi

    if [ -z "$PYTHONBIN" ] || [ ! -x "$PYTHONBIN" ]; then
        echo "ERROR: Could not find a suitable Python 3.6+ installation"
        echo "Available Python installations:"
        find /opt/csw/bin /usr/bin /usr/local/bin -name "python*" -executable 2>/dev/null || true
        
        echo ""
        echo "=== PYTHON INSTALLATION OPTIONS ==="
        echo ""
        echo "Configured Python version: $PYTHONVER"
        echo "Preferred Python version: $PREFERRED_PYTHON_VERSION"
        echo ""
        echo "Option 1: Install Python via IPS (recommended):"
        if command -v pkg >/dev/null 2>&1; then
            echo "  Available Python packages in IPS:"
            pkg list -a | grep "runtime/python" | head -5 || echo "  None found"
            echo ""
            echo "  Try these commands (in order of preference):"
            echo "    sudo pkg install runtime/python-${PYTHON_MAJOR}${PYTHON_MAJOR_MINOR#*.}"  # Configured version
            echo "    sudo pkg install runtime/python-313"
            echo "    sudo pkg install runtime/python-312"
            echo "    sudo pkg install runtime/python-311"
            echo "    sudo pkg install runtime/python-310"
            echo "    sudo pkg install runtime/python-39"
        else
            echo "  IPS not available on this system"
        fi
        
        echo ""
        echo "Option 2: Build Python from source:"
        echo "  This script can attempt to build Python $PYTHONVER from source (configured version)"
        echo "  This requires GCC and development tools to be installed"
        echo ""
        
        if [ $NO_INTERACTION -eq 1 ]; then
            echo "Non-interactive mode - exiting without Python"
            exit 1
        else
            read -r -p "Would you like to attempt building Python $PYTHONVER from source? [y/N] " build_python
            if [[ $build_python =~ ^(yes|y|Y)$ ]]; then
                echo "Attempting to build Python from source..."
                build_python_from_source
                
                # Re-check for Python after build (look for configured version first)
                check_paths=(
                    "/usr/local/bin/python$PREFERRED_PYTHON_VERSION"
                    "/usr/local/bin/python$PYTHON_MAJOR"
                    "/usr/local/bin/python3"
                    "/usr/local/bin/python3.13" "/usr/local/bin/python3.12" 
                    "/usr/local/bin/python3.11" "/usr/local/bin/python3.10" "/usr/local/bin/python3.9"
                )
                
                for py_path in "${check_paths[@]}"; do
                    if [ -x "$py_path" ]; then
                        PYTHONBIN="$py_path"
                        echo "✓ Found newly built Python at: $PYTHONBIN"
                        break
                    fi
                done
                
                if [ -z "$PYTHONBIN" ]; then
                    echo "ERROR: Python build failed"
                    exit 1
                fi
            else
                echo "Exiting - Python 3.6+ is required to build NCPA"
                exit 1
            fi
        fi
    fi

    echo "Using Python: $PYTHONBIN"
    $PYTHONBIN --version

    # Validate that the selected Python works
    if ! $PYTHONBIN -c "import sys; print('Python validation successful')" 2>/dev/null; then
        echo "ERROR: Selected Python $PYTHONBIN failed basic validation"
        exit 1
    fi

    # Install pip if not available - handle different Python versions
    if ! $PYTHONBIN -m pip --version >/dev/null 2>&1; then
        echo "Installing pip..."
        
        # Get Python version to determine which get-pip.py to use
        py_version=$($PYTHONBIN --version 2>&1 | sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -1)
        major=$(echo "$py_version" | cut -d. -f1)
        minor=$(echo "$py_version" | cut -d. -f2)
        
        if [ "$major" -eq 3 ] && [ "$minor" -lt 6 ]; then
            # For Python < 3.6, use the legacy pip installer
            echo "Using legacy pip installer for Python $py_version"
            pip_url="https://bootstrap.pypa.io/pip/$py_version/get-pip.py"
        else
            # For Python >= 3.6, use the modern pip installer
            echo "Using modern pip installer for Python $py_version"
            pip_url="https://bootstrap.pypa.io/get-pip.py"
        fi
        
        # Download and install pip
        if command -v wget >/dev/null 2>&1; then
            wget -O /tmp/get-pip.py "$pip_url"
        elif command -v curl >/dev/null 2>&1; then
            curl -k -o /tmp/get-pip.py "$pip_url"
        else
            echo "ERROR: Neither wget nor curl available to download pip"
            exit 1
        fi
        
        if [ -f /tmp/get-pip.py ]; then
            $PYTHONBIN /tmp/get-pip.py --user
            rm -f /tmp/get-pip.py
        else
            echo "ERROR: Failed to download pip installer"
            exit 1
        fi
    fi

    # Export PYTHONBIN for use by the main build script and other processes
    export PYTHONBIN
    export PYTHONVER
    export PYTHON_MAJOR_MINOR
    export PREFERRED_PYTHON_VERSION

    # Add debug output for Python detection
    echo "=== FINAL PYTHON CONFIGURATION ==="
    echo "  Configured Python version: $PYTHONVER"
    echo "  Preferred Python version: $PREFERRED_PYTHON_VERSION"
    echo "  Selected PYTHONBIN: $PYTHONBIN"
    echo "  Actual Python version: $($PYTHONBIN --version 2>&1)"
    
    # Check if we got the preferred version
    actual_version=$($PYTHONBIN --version 2>&1 | sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -1)
    if [ "$actual_version" = "$PREFERRED_PYTHON_VERSION" ]; then
        echo "  ✓ Using configured Python version: $actual_version"
    elif [ "${actual_version%.*}" = "${PREFERRED_PYTHON_VERSION%.*}" ]; then
        echo "  ⚠ Using compatible Python version: $actual_version (configured: $PREFERRED_PYTHON_VERSION)"
    else
        echo "  ⚠ Using different Python version: $actual_version (configured: $PREFERRED_PYTHON_VERSION)"
    fi
    
    echo "  Python executable path: $(which $($PYTHONBIN -c 'import sys; print(sys.executable.split("/")[-1])') 2>/dev/null || echo 'unknown')"
    echo "===================================="
    echo ""
    
    # Run Python debug script if available
    if [ -f "$BUILD_DIR/solaris/debug_python.sh" ]; then
        echo "Running Python debug script..."
        "$BUILD_DIR/solaris/debug_python.sh"
        echo ""
    fi

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
    
    # Check for readline library
    echo "Checking for readline library..."
    readline_found=false
    for readline_path in /usr/lib/libreadline.so* /lib/libreadline.so* /usr/local/lib/libreadline.so* /opt/csw/lib/libreadline.so*; do
        if [ -f "$readline_path" ]; then
            echo "✓ readline library found: $readline_path"
            readline_found=true
            break
        fi
    done
    if [ "$readline_found" = false ]; then
        echo "✗ readline library not found - Python may have limited interactive features"
    fi
    
    # Check for ncurses library
    echo "Checking for ncurses library..."
    ncurses_found=false
    for ncurses_path in /usr/lib/libncurses.so* /lib/libncurses.so* /usr/local/lib/libncurses.so* /opt/csw/lib/libncurses.so*; do
        if [ -f "$ncurses_path" ]; then
            echo "✓ ncurses library found: $ncurses_path"
            ncurses_found=true
            break
        fi
    done
    if [ "$ncurses_found" = false ]; then
        echo "✗ ncurses library not found - some terminal features may not work"
    fi
    
    # Check for other critical libraries
    check_system_library "z" "zlib compression library"
    check_system_library "ffi" "libffi library" 
    check_system_library "bz2" "bzip2 compression library"
    
    echo "Library verification complete."

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

# Main execution
main() {
    echo "=========================================="
    echo "NCPA Solaris Setup Script"
    echo "=========================================="
    echo "This script will install prerequisites and configure Python for NCPA build"
    echo ""
    
    # Ensure we have the proper permissions
    if [ "$(id -u)" -eq 0 ]; then
        echo "WARNING: Running as root. Some package installations may require sudo anyway."
    fi
    
    # Install prerequisites
    install_prereqs
    
    echo ""
    echo "=========================================="
    echo "Setup completed successfully!"
    echo "Python binary: $PYTHONBIN"
    echo "Python version: $($PYTHONBIN --version 2>&1)"
    echo "=========================================="
}

# Only run main if script is executed directly (not sourced)
if [ "${BASH_SOURCE[0]}" = "${0}" ] || [ -z "${BASH_SOURCE[0]}" ]; then
    main "$@"
fi
