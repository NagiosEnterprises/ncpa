#!/usr/bin/env bash

echo -e "***** macos/installers.sh"

get_original_user() {
    if [[ $EUID -eq 0 ]]; then
        # Running as root, get the original user
        echo ${SUDO_USER:-$USER}
    else
        # Not running as root
        echo $USER
    fi
}

# Run command as the original user (not root)
run_as_user() {
    local original_user=$(get_original_user)
    if [[ $EUID -eq 0 && -n "$SUDO_USER" ]]; then
        # Running as root via sudo, run as original user
        sudo -u "$original_user" "$@"
    else
        # Not running as root, run normally
        "$@"
    fi
}

set -e
trap 'echo "Error on line $LINENO"; exit 1' ERR

# Dynamic OpenSSL path detection and version pinning (always run Homebrew as user)
REQUIRED_OPENSSL_VERSION="3"
OPENSSL_PREFIX=$(run_as_user brew --prefix openssl@${REQUIRED_OPENSSL_VERSION} 2>/dev/null || run_as_user brew --prefix openssl)
INSTALLED_OPENSSL_VERSION=$(run_as_user brew list --versions openssl@${REQUIRED_OPENSSL_VERSION} | awk '{print $2}')
if [[ -z "$INSTALLED_OPENSSL_VERSION" ]]; then
    echo "Required OpenSSL version not found. Installing..."
    run_as_user brew install openssl@${REQUIRED_OPENSSL_VERSION}
    OPENSSL_PREFIX=$(run_as_user brew --prefix openssl@${REQUIRED_OPENSSL_VERSION})
fi
export LDFLAGS="-L$OPENSSL_PREFIX/lib"
export CPPFLAGS="-I$OPENSSL_PREFIX/include"

# Scripts to install homebrew and dev tools, and update python libraries

# Source version configuration
BUILD_DIR_FOR_VERSION=$(dirname "$(dirname "$0")")
source "$BUILD_DIR_FOR_VERSION/version_config.sh"

# Load utilities to fix dynamic libs
. $BUILD_DIR/macos/linkdynlibs.sh
os_version=$(sw_vers -productVersion)
os_major_version=$(echo $os_version | cut -f1 -d.)
os_minor_version=$(echo $os_version | cut -f2 -d.)

# Utility scripts

check_python() {
    local python_cmd=$1
    if command -v $python_cmd &> /dev/null; then
        local version=$($python_cmd --version 2>&1 | cut -d' ' -f2)
        echo "Found Python: $python_cmd (version $version)" >&2
        return 0
    fi
    return 1
}

find_system_python() {
    # Check for common Python installations
    for python_cmd in python3 python python3.15 python3.14 python3.13 python3.12 python3.11 python3.10 python3.9 python3.8; do
        if check_python $python_cmd 2>/dev/null; then
            echo $python_cmd
            return 0
        fi
    done
    return 1
}

# Installs tools needed to make and install dependencies
install_devtools() {
    echo -e "\n***** macos/installers.sh - install_devtools()"
    echo -e "    - Installing Homebrew and dev tools on MacOS $os_version..."

    if [[ -z $(xcode-select --version 2>/dev/null) ]]; then
        echo -e "\n    - Installing xcode command line tools..."
        xcode-select --install
    else
        echo -e "\n    - Xcode command line tools already installed"
    fi

    local original_user=$(get_original_user)
    
    # Check for Homebrew in common locations
    BREWBIN=""
    for brew_path in "/opt/homebrew/bin/brew" "/usr/local/bin/brew" "/home/linuxbrew/.linuxbrew/bin/brew"; do
        if [[ -x "$brew_path" ]]; then
            BREWBIN="$brew_path"
            break
        fi
    done
    
    if [[ -z "$BREWBIN" ]]; then
        echo -e "    - Installing Homebrew package manager..."
        if [[ "$os_major_version" == "10" ]]; then
            export HOMEBREW_NO_INSTALL_FROM_API=1
        fi
        # Install Homebrew as the original user, not root
        run_as_user /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Find the installed brew binary
        for brew_path in "/opt/homebrew/bin/brew" "/usr/local/bin/brew"; do
            if [[ -x "$brew_path" ]]; then
                BREWBIN="$brew_path"
                break
            fi
        done
    else
        echo -e "\n    - Homebrew already installed at $BREWBIN"
    fi

    # Make sure we have the brew binary
    if [[ -z "$BREWBIN" ]]; then
        echo -e "ERROR! Could not find or install Homebrew"
        return 1
    fi
    
    # Export BREWBIN for use in other functions
    export BREWBIN
    
    # Set up environment for this session
    eval "$(run_as_user "$BREWBIN" shellenv)"
    export HOMEBREW_PREFIX=$(run_as_user "$BREWBIN" --prefix)

    echo -e "    - Installing misc brew packages: pkg-config xz gdbm mpdecimal..."
    run_as_user "$BREWBIN" update
    run_as_user "$BREWBIN" install pkg-config xz gdbm mpdecimal
    if [[ "$os_major_version" == "10" ]]; then
        echo -e "    - Installing libffi (MacOS v10.x only)..."
        run_as_user "$BREWBIN" install libffi
    fi
    
    # Create symlink for mpdecimal library if it doesn't exist where cx_Freeze expects it
    local mpdecimal_path=$(run_as_user "$BREWBIN" --prefix mpdecimal 2>/dev/null)
    if [[ -n "$mpdecimal_path" && -f "$mpdecimal_path/lib/libmpdec.dylib" ]]; then
        echo -e "    - Setting up mpdecimal library symlink..."
        local target_dir="/usr/local/opt/mpdecimal/lib"
        if [[ ! -d "$target_dir" ]]; then
            sudo mkdir -p "$target_dir"
        fi
        if [[ ! -f "$target_dir/libmpdec.4.0.0.dylib" ]]; then
            sudo ln -sf "$mpdecimal_path/lib/libmpdec.dylib" "$target_dir/libmpdec.4.0.0.dylib"
        fi
    fi

}

verify_or_install_python() {
    echo -e "\n***** macos/installers.sh - verify_or_install_python()"
    echo -e "    - Checking for system Python installation..."

    local python_cmd=$(find_system_python 2>/dev/null)
    if [[ $? -eq 0 && -n "$python_cmd" ]]; then
        echo -e "    - Using system Python: $python_cmd"
        
        # Set the Python command and binary paths
        export PYTHONCMD="$python_cmd"
        export PYTHONBIN="$python_cmd"
        
        # Get Python version
        local python_version=$($python_cmd --version 2>&1 | cut -d' ' -f2)
        export PYTHONVER="$python_version"
        
        # Set up Homebrew environment if we have a brew binary
        if [[ -n "$BREWBIN" ]]; then
            eval "$(run_as_user "$BREWBIN" shellenv)"
            export HOMEBREW_PREFIX=$(run_as_user "$BREWBIN" --prefix)
        elif command -v brew &> /dev/null; then
            eval "$(brew shellenv)"
            export HOMEBREW_PREFIX=$(brew --prefix)
        else
            # Fallback to common prefix
            export HOMEBREW_PREFIX="/usr/local"
        fi
        
        echo -e "    - Python version: $python_version"
        echo -e "    - Debug: PYTHONCMD='$PYTHONCMD', PYTHONBIN='$PYTHONBIN'"
        
        # Check if pip is available
        if ! $python_cmd -m pip --version &> /dev/null; then
            echo -e "    - Installing pip..."
            $python_cmd -m ensurepip --upgrade
        fi
        
        return 0
    else
        echo -e "    - No system Python found, installing via Homebrew..."
        
        # Make sure Homebrew is installed
        if [[ -z "$BREWBIN" ]]; then
            echo -e "    - Installing Homebrew first..."
            install_devtools
        fi
        
        # Install Python via Homebrew as the original user
        echo -e "    - Installing Python 3 via Homebrew..."
        run_as_user "$BREWBIN" install python3
        
        # Set up environment after installation
        eval "$(run_as_user "$BREWBIN" shellenv)"
        
        # Find the newly installed Python
        local python_cmd=$(find_system_python 2>/dev/null)
        if [[ $? -eq 0 && -n "$python_cmd" ]]; then
            echo -e "    - Successfully installed Python: $python_cmd"
            
            # Set the Python command and binary paths
            export PYTHONCMD="$python_cmd"
            export PYTHONBIN="$python_cmd"
            
            # Get Python version
            local python_version=$($python_cmd --version 2>&1 | cut -d' ' -f2)
            export PYTHONVER="$python_version"
            
            # Set up Homebrew environment
            eval "$(run_as_user "$BREWBIN" shellenv)"
            export HOMEBREW_PREFIX=$(run_as_user "$BREWBIN" --prefix)
            
            echo -e "    - Python version: $python_version"
            echo -e "    - Debug: PYTHONCMD='$PYTHONCMD', PYTHONBIN='$PYTHONBIN'"
            return 0
        else
            echo -e "ERROR! Python installation failed!"
            echo -e "Please install Python 3.8+ manually:"
            echo -e "  Option 1: Download from https://www.python.org/downloads/"
            echo -e "  Option 2: Install via Homebrew: brew install python3"
            echo -e "********************************************\n\n"
            return 1
        fi
    fi
}

# Requires globals $PYTHONBIN, $PYTHONVER, $PYTHONCMD and $BUILD_DIR
update_py_packages() {
    echo -e "\n***** macos/installers.sh - update_py_packages()"
    echo -e "    - Debug: PYTHONCMD='$PYTHONCMD', PYTHONBIN='$PYTHONBIN'"
    
    # Check if we're in virtual environment mode
    if [[ -n "$VENV_MANAGER" && -n "$VENV_NAME" ]]; then
        echo -e "    - Using virtual environment approach via venv_manager"
        if ! "$VENV_MANAGER" install_packages; then
            echo -e "ERROR! Failed to install Python packages via venv_manager"
            return 1
        fi
        
        # Get the virtual environment Python executable
        local venv_python=$("$VENV_MANAGER" get_python_path)
        if [[ -z "$venv_python" ]]; then
            echo -e "ERROR! Could not get virtual environment Python path"
            return 1
        fi
        
        # Update our Python commands to use the venv Python
        export PYTHONBIN="$venv_python"
        export PYTHONCMD="$venv_python"
        echo -e "    - Updated PYTHONBIN to virtual environment: $PYTHONBIN"
        
        # Find the virtual environment site-packages directory
        local site_packages_dir=$("$venv_python" -c "import site; print(site.getsitepackages()[0])")
        echo "    Virtual environment site packages directory: $site_packages_dir"
        
        # Check if cx_Freeze is installed in the virtual environment
        local cx_freeze_path=$("$venv_python" -c "import cx_Freeze; print(cx_Freeze.__file__)" 2>/dev/null | sed 's|/__init__.py||g')
    else
        echo -e "    - Using legacy system Python approach"
        
        # Validate that we have a valid Python command
        if [[ -z "$PYTHONBIN" ]]; then
            echo -e "ERROR! PYTHONBIN is not set!"
            return 1
        fi
        
        if ! command -v "$PYTHONBIN" &> /dev/null; then
            echo -e "ERROR! Python command '$PYTHONBIN' not found!"
            return 1
        fi
        
        # Install/upgrade pip and packages as the original user
        # Use --break-system-packages and --user to handle externally managed environments
        echo -e "    - Upgrading pip..."
        run_as_user "$PYTHONBIN" -m pip install --upgrade pip --break-system-packages --user
        
        echo -e "    - Installing Python packages from requirements..."
        run_as_user "$PYTHONBIN" -m pip install -r "$BUILD_DIR/resources/require.txt" --upgrade --break-system-packages --user
        
        # Add user's Python bin directory to PATH
        local user_python_bin=$(run_as_user "$PYTHONBIN" -c "import site; import os; print(os.path.join(site.USER_BASE, 'bin'))")
        echo "    Adding user Python bin directory to PATH: $user_python_bin"
        export PATH="$user_python_bin:$PATH"

        # Find the Python site-packages directory (check user packages first)
        local site_packages_dir=$(run_as_user "$PYTHONBIN" -c "import site; print(site.getusersitepackages())")
        echo "    User site packages directory: $site_packages_dir"

        # Check if cx_Freeze is installed and get its path (check user packages first)
        local cx_freeze_path=$(run_as_user "$PYTHONBIN" -c "import cx_Freeze; print(cx_Freeze.__file__)" 2>/dev/null | sed 's|/__init__.py||g')
        
        # If not found in user packages, check system packages
        if [[ -z "$cx_freeze_path" ]]; then
            local system_site_packages=$(run_as_user "$PYTHONBIN" -c "import site; print(site.getsitepackages()[0])")
            echo "    Checking system site packages: $system_site_packages"
            cx_freeze_path=$(run_as_user "$PYTHONBIN" -c "import sys; sys.path.insert(0, '$system_site_packages'); import cx_Freeze; print(cx_Freeze.__file__)" 2>/dev/null | sed 's|/__init__.py||g')
        fi
    fi
    
    if [[ -n "$cx_freeze_path" ]]; then
        echo "    cx_Freeze path: $cx_freeze_path"
        
        local cxlibpath="$cx_freeze_path/bases"
        echo "    cxlibpath: $cxlibpath"

        # Find Python's lib-dynload directory using a more robust method
        local python_lib_dynload=$(run_as_user "$PYTHONBIN" -c "import sys; import os; import sysconfig; print(os.path.join(sysconfig.get_path('stdlib'), 'lib-dynload'))")
        echo "    Python lib-dynload: $python_lib_dynload"
        
        # If that doesn't work, try the traditional approach
        if [[ ! -d "$python_lib_dynload" ]]; then
            python_lib_dynload=$(run_as_user "$PYTHONBIN" -c "import sys; import os; version = '{}.{}'.format(sys.version_info[0], sys.version_info[1]); print(os.path.join(sys.prefix, 'lib', 'python' + version, 'lib-dynload'))")
            echo "    Python lib-dynload (fallback): $python_lib_dynload"
        fi

        # Only proceed if both directories exist
        if [[ -d "$python_lib_dynload" && -d "$cxlibpath" ]]; then
            echo -e "    - Updating cx_freeze lib-dynload with system Python libraries..."

            # For MacOS 11+ libraries need special treatment
            if [[ "$os_major_version" != "10" ]]; then
                if [ ! -d "$python_lib_dynload/../lib-dynload_orig" ]; then
                    sudo mkdir -p "$python_lib_dynload/../lib-dynload_orig"
                    sudo cp "$python_lib_dynload"/* "$python_lib_dynload/../lib-dynload_orig/" 2>/dev/null || true
                fi
                
                # Define paths for dependency link fixer (only if functions exist)
                if declare -f setPaths >/dev/null 2>&1; then
                    echo "    - Setting up library paths for dependency fixes..."
                    
                    # Ensure required environment variables are set
                    if [[ -z "$HOMEBREW_PREFIX" ]]; then
                        if [[ -n "$BREWBIN" ]]; then
                            export HOMEBREW_PREFIX=$(run_as_user "$BREWBIN" --prefix)
                        else
                            export HOMEBREW_PREFIX="/usr/local"
                        fi
                    fi
                    
                    # Also ensure HOMEBREW_CELLAR is set (required by setPaths)
                    if [[ -z "$HOMEBREW_CELLAR" ]]; then
                        export HOMEBREW_CELLAR="$HOMEBREW_PREFIX/Cellar"
                    fi
                    
                    # Ensure PYTHONVER is set (required by setPaths)
                    if [[ -z "$PYTHONVER" && -n "$PYTHONCMD" ]]; then
                        export PYTHONVER=$($PYTHONCMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
                    fi
                    
                    echo "    - Environment: PYTHONVER=$PYTHONVER, HOMEBREW_PREFIX=$HOMEBREW_PREFIX, HOMEBREW_CELLAR=$HOMEBREW_CELLAR"
                    
                    # Call setPaths with the python lib-dynload directory
                    setPaths "$python_lib_dynload"
                    
                    # Note: Library dependency fixing will be handled later by package.sh
                    # after cx_Freeze has created the build directory
                    echo "    - Library paths configured for build process"
                else
                    echo "    - Warning: setPaths function not found, skipping library path setup"
                fi
            fi

            if [ ! -d "$cxlibpath/lib-dynload_orig" ]; then
                sudo mkdir -p "$cxlibpath/lib-dynload_orig"
                sudo cp "$cxlibpath/lib-dynload"/* "$cxlibpath/lib-dynload_orig/" 2>/dev/null || true
            fi

            # Link python's lib-dynload to cx_freeze lib-dynload
            sudo cp "$python_lib_dynload"/* "$cxlibpath/lib-dynload/" 2>/dev/null || true
        else
            echo "    - Warning: Could not find lib-dynload directories, skipping library updates"
        fi
    else
        echo "    - cx_Freeze not found, skipping library updates"
    fi
}

# Ensure all required libraries exist for cx_Freeze
ensure_cx_freeze_libraries() {
    echo -e "\n***** macos/installers.sh - ensure_cx_freeze_libraries()"
    
    # Define required libraries and their packages
    # Removed all OpenSSL-related logic and symlink creation. Only mpdecimal, sqlite, and xz logic should remain if needed.
}
