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

# Virtual environment integration
VENV_MANAGER="$BUILD_DIR_FOR_VERSION/venv_manager.sh"
export VENV_NAME="${VENV_NAME:-ncpa-build-solaris}"

# Global configuration
PREFERRED_PYTHON_VERSION="$PYTHON_MAJOR_MINOR"  # Use version from config (e.g., "3.13")
NO_INTERACTION="${NO_INTERACTION:-0}"  # Default to interactive mode if not set
SKIP_PYTHON="${SKIP_PYTHON:-0}"  # Skip Python setup if using venv

# Build directory for referencing other scripts
BUILD_DIR="${BUILD_DIR_FOR_VERSION}"

# Debug output for version configuration
echo "=== Solaris Setup Configuration ==="
echo "PYTHONVER: $PYTHONVER"
echo "PYTHON_MAJOR_MINOR: $PYTHON_MAJOR_MINOR"
echo "PREFERRED_PYTHON_VERSION: $PREFERRED_PYTHON_VERSION"
echo "SSLVER: $SSLVER"
echo "ZLIBVER: $ZLIBVER"
echo "SKIP_PYTHON: $SKIP_PYTHON"
echo "VENV_NAME: $VENV_NAME"
echo "================================"
echo ""

# If using virtual environment (recommended), skip Python detection
if [ "$SKIP_PYTHON" -eq 1 ]; then
    echo "Skipping Python setup - using virtual environment"
    if [ -n "$PYTHONBIN" ] && [ -x "$PYTHONBIN" ]; then
        echo "Using Python from virtual environment: $PYTHONBIN"
        echo "Python version: $($PYTHONBIN --version 2>&1)"
    else
        echo "WARNING: PYTHONBIN not set or not executable: $PYTHONBIN"
    fi
    
    # Check version of Solaris for later use
    SOLARIS_VER=$(uname -r | cut -d. -f2)
    ARCH=$(arch)
else
    echo "WARNING: Virtual environment not detected, falling back to system Python detection"
    # Keep the original Python detection code as fallback (but this should rarely be used)
    PYTHONBIN=""
    
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

    # Check version of Solaris for the fallback path
    SOLARIS_VER=$(uname -r | cut -d. -f2)
    ARCH=$(arch)
fi  # End of Python detection conditional

update_py_packages() {
    # Install Python packages in virtual environment (Solaris 11+)
    if [ "$SOLARIS_VER" -ge 11 ]; then
        echo "Installing Python packages for Solaris 11 in virtual environment..."
        
        # Check if we have a working Python in venv
        if [ -z "$PYTHONBIN" ] || [ ! -x "$PYTHONBIN" ]; then
            echo "ERROR: No Python binary available from virtual environment"
            return 1
        fi
        
        echo "Using Python from venv: $PYTHONBIN ($($PYTHONBIN --version 2>&1))"
        
        # Check if we're in a virtual environment (should be true)
        if [ -n "$VIRTUAL_ENV" ]; then
            echo "✓ Virtual environment detected: $VIRTUAL_ENV"
            echo "✓ No externally-managed-environment issues in venv"
        else
            echo "WARNING: VIRTUAL_ENV not set - may not be in virtual environment"
        fi
        
        # Virtual environments don't have externally-managed restrictions
        echo "Installing packages directly in virtual environment (no --user or --break-system-packages needed)"
        
        # Check if pip is available in venv
        if ! "$PYTHONBIN" -m pip --version >/dev/null 2>&1; then
            echo "ERROR: pip not available in virtual environment"
            return 1
        fi
        
        # Upgrade pip first
        echo "Upgrading pip in virtual environment..."
        if ! "$PYTHONBIN" -m pip install --upgrade pip; then
            echo "WARNING: Could not upgrade pip, continuing with existing version"
        fi
        
        # Install required packages
        echo "Installing required Python packages in virtual environment..."
        solaris_build_requirements="$BUILD_DIR/resources/require-solaris-build.txt"
        solaris_requirements="$BUILD_DIR/resources/require-solaris.txt"
        standard_requirements="$BUILD_DIR/resources/require.txt"
        
        # Simple package installation function for venv (no complex fallbacks needed)
        install_venv_package() {
            local pkg="$1"
            echo "Installing $pkg in venv..."
            if "$PYTHONBIN" -m pip install "$pkg"; then
                echo "✓ Successfully installed $pkg"
                return 0
            else
                echo "✗ Failed to install $pkg"
                return 1
            fi
        }
        
        # Try requirements file first - prefer build-specific over runtime
        if [ -f "$solaris_build_requirements" ]; then
            echo "Installing from Solaris build requirements: $solaris_build_requirements"
            if "$PYTHONBIN" -m pip install -r "$solaris_build_requirements" --upgrade; then
                echo "✓ Successfully installed packages from require-solaris-build.txt"
            else
                echo "Batch installation failed, trying individual packages..."
                while IFS= read -r pkg; do
                    if [ -n "$pkg" ] && [ "${pkg#\#}" = "$pkg" ]; then  # Skip empty lines and comments
                        install_venv_package "$pkg"
                    fi
                done < "$solaris_build_requirements"
            fi
            
            # Try to install SSL support after core packages
            echo "Attempting to install SSL support packages..."
            ssl_installed=false
            for ssl_pkg in pyOpenSSL cryptography; do
                echo "Trying to install $ssl_pkg..."
                if install_venv_package "$ssl_pkg"; then
                    echo "✓ Successfully installed $ssl_pkg"
                    ssl_installed=true
                    break  # If one works, we're good
                else
                    echo "Failed to install $ssl_pkg, will try next option"
                fi
            done
            
            if [ "$ssl_installed" = false ]; then
                echo "WARNING: No SSL Python libraries installed successfully."
                echo "NCPA will attempt to use system openssl command for certificate generation."
                echo "Make sure 'openssl' is available in PATH at runtime."
            fi
            
        elif [ -f "$solaris_requirements" ]; then
            echo "Installing from Solaris-specific requirements: $solaris_requirements"
            if "$PYTHONBIN" -m pip install -r "$solaris_requirements" --upgrade; then
                echo "✓ Successfully installed packages from require-solaris.txt"
            else
                echo "Batch installation failed, trying individual packages..."
                while IFS= read -r pkg; do
                    if [ -n "$pkg" ] && [ "${pkg#\#}" = "$pkg" ]; then  # Skip empty lines and comments
                        install_venv_package "$pkg"
                    fi
                done < "$solaris_requirements"
            fi
        elif [ -f "$standard_requirements" ]; then
            echo "Installing from standard requirements: $standard_requirements"
            # For Solaris, replace cryptography with pyOpenSSL to avoid Rust dependency
            echo "Filtering out cryptography and ensuring pyOpenSSL for Solaris compatibility..."
            temp_req="/tmp/require-solaris-venv.txt"
            grep -v "^cryptography" "$standard_requirements" | grep -v "^pyOpenSSL" > "$temp_req"
            echo "pyOpenSSL" >> "$temp_req"
            
            if "$PYTHONBIN" -m pip install -r "$temp_req" --upgrade; then
                echo "✓ Successfully installed packages from require.txt"
            else
                echo "Batch installation failed, trying individual packages..."
                while IFS= read -r pkg; do
                    if [ -n "$pkg" ] && [ "${pkg#\#}" = "$pkg" ]; then  # Skip empty lines and comments
                        install_venv_package "$pkg"
                    fi
                done < "$temp_req"
            fi
            rm -f "$temp_req"
        else
            echo "WARNING: No requirements file found, installing core packages individually..."
            # Install essential packages for NCPA
            for pkg in cx_Freeze psutil requests Jinja2 flask werkzeug gevent appdirs packaging; do
                install_venv_package "$pkg"
            done
            
            # Try to install SSL support separately  
            echo "Attempting to install SSL support..."
            ssl_installed=false
            for ssl_pkg in pyOpenSSL cryptography; do
                echo "Trying to install $ssl_pkg..."
                if install_venv_package "$ssl_pkg"; then
                    echo "✓ Successfully installed $ssl_pkg"
                    ssl_installed=true
                    break  # If one works, we're good
                else
                    echo "Failed to install $ssl_pkg, will try next option"
                fi
            done
            
            if [ "$ssl_installed" = false ]; then
                echo "WARNING: No SSL Python libraries installed successfully."
                echo "NCPA will attempt to use system openssl command for certificate generation."
                echo "Make sure 'openssl' is available in PATH at runtime."
            fi
        fi
        
        echo "✓ Python package installation completed in virtual environment"
    else
        echo "ERROR: Solaris 10 and older are not supported."
        echo "Please upgrade to Solaris 11 or later."
        exit 1
    fi
}

install_prereqs() {
    echo "Installing system prerequisites for Solaris..."
    echo "Note: Python packages will be installed in virtual environment"

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

    # Install essential system dependencies only (Python handled by venv)
    echo "Installing essential system dependencies..."
    
    # Install core build tools
    echo "Installing development tools..."
    safe_install_package "gcc4core" "GCC compiler core"
    safe_install_package "gcc4g++" "GCC C++ compiler"
    safe_install_package "make" "GNU make"
    safe_install_package "gmake" "GNU make alternative"
    safe_install_package "pkgconfig" "pkg-config utility"
    
    # Install core system libraries that Python may need
    echo "Installing system libraries..."
    safe_install_package "zlib" "zlib compression library"
    safe_install_package "libffi" "libffi library"
    safe_install_package "bzip2" "bzip2 compression"
    safe_install_package "readline" "readline library"
    safe_install_package "ncurses" "ncurses library"
    safe_install_package "openssl_devel" "OpenSSL development libraries"
    safe_install_package "libssl_devel" "SSL development libraries"
    
    # Try IPS packages for core dependencies
    if command -v pkg >/dev/null 2>&1; then
        echo "Installing core dependencies via IPS..."
        pkg install --accept library/zlib 2>/dev/null || echo "zlib already installed or not available"
        pkg install --accept library/libffi 2>/dev/null || echo "libffi already installed or not available"
        pkg install --accept library/security/openssl 2>/dev/null || echo "openssl already installed or not available"
        pkg install --accept developer/gcc 2>/dev/null || echo "gcc already installed or not available"
        pkg install --accept developer/build/gnu-make 2>/dev/null || echo "make already installed or not available"
    fi
    
    # Update PATH to include common tool locations
    export PATH=/opt/csw/bin:/opt/csw/sbin:/usr/sfw/bin:/usr/ccs/bin:/usr/bin:/usr/local/bin:$PATH
    export LD_LIBRARY_PATH=/opt/csw/lib:/usr/lib:$LD_LIBRARY_PATH
    export PKG_CONFIG_PATH=/opt/csw/lib/pkgconfig:/usr/lib/pkgconfig:$PKG_CONFIG_PATH

    # Verify critical build tools
    echo "Verifying critical build tools..."
    
    # Check for make or gmake
    if command -v make >/dev/null 2>&1; then
        echo "✓ make available: $(which make)"
    elif command -v gmake >/dev/null 2>&1; then
        echo "✓ gmake available: $(which gmake)"
        # Create a make symlink if possible
        if [ ! -e /opt/csw/bin/make ] && [ -w /opt/csw/bin ]; then
            ln -s "$(which gmake)" /opt/csw/bin/make
            echo "Created make symlink to gmake"
        fi
    else
        echo "✗ Neither make nor gmake found - build may fail"
    fi
    
    # Check for gcc
    if command -v gcc >/dev/null 2>&1; then
        echo "✓ gcc available: $(which gcc)"
    else
        echo "✗ gcc not found - this may cause build issues"
    fi
    
    # Setup nagios user and group
    echo "Setting up nagios user and group..."
    if ! getent group nagios >/dev/null 2>&1; then
        groupadd nagios
    fi
    if ! getent passwd nagios >/dev/null 2>&1; then
        useradd -g nagios -d /usr/local/ncpa -s /bin/false nagios
    fi

    # Only install Python packages if not using venv (venv handles this)
    if [ "$SKIP_PYTHON" -eq 0 ]; then
        echo "Installing Python packages (fallback mode)..."
        update_py_packages
    else
        echo "Skipping Python package installation - will be handled by virtual environment"
    fi

}

# Main execution
main() {
    echo "=========================================="
    echo "NCPA Solaris Setup Script (Virtual Environment)"
    echo "=========================================="
    echo "This script will install system prerequisites for NCPA build"
    echo "Python packages will be managed by virtual environment"
    echo ""
    
    # Ensure we have the proper permissions
    if [ "$(id -u)" -eq 0 ]; then
        echo "WARNING: Running as root. Some package installations may require sudo anyway."
    fi
    
    # Install system prerequisites only (Python packages handled by venv)
    install_prereqs
    
    echo ""
    echo "=========================================="
    echo "Solaris system setup completed successfully!"
    echo "Virtual environment will handle Python packages"
    echo "=========================================="
}

# Only run main if script is executed directly (not sourced)
if [ "${BASH_SOURCE[0]}" = "${0}" ] || [ -z "${BASH_SOURCE[0]}" ]; then
    main "$@"
fi
