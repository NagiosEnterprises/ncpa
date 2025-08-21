#!/usr/bin/env bash

echo -e "***** macos/setup.sh"

get_original_user() {
    if [[ $EUID -eq 0 ]]; then
        echo ${SUDO_USER:-$USER}
    else
        echo $USER
    fi
}

run_as_user() {
    local original_user=$(get_original_user)
    if [[ $EUID -eq 0 && -n "$SUDO_USER" ]]; then
        sudo -u "$original_user" "$@"
    else
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

# Virtual environment integration
VENV_MANAGER="$BUILD_DIR/venv_manager.sh"
export VENV_NAME="${VENV_NAME:-ncpa-build-macos}"

# Globals - defined in build.sh and version_config.sh
#     PYTHONVER, SSLVER, ZLIBVER, SKIP_PYTHON

# Load some installers and support functions
. $BUILD_DIR/macos/installers.sh

# Skip Python detection if using virtual environment (recommended)
SKIP_PYTHON="${SKIP_PYTHON:-0}"

# Find system Python - will be set by verify_python function (fallback mode)
PYTHONCMD=""
PYTHONBIN=""

# Set AGENT_DIR if not already set
if [[ -z "$AGENT_DIR" ]]; then
    AGENT_DIR="$BUILD_DIR/../agent"
fi

# Automatically install Python requirements in venv after setup
if [ -n "$VENV_MANAGER" ] && [ -x "$VENV_MANAGER" ]; then
    "$VENV_MANAGER" install-requirements
fi

echo -e "***** macos/setup.sh - SKIP_PYTHON: $SKIP_PYTHON"

set +e

install_prereqs() {
    echo -e "***** macos/setup.sh - install_prereqs()..."
    echo -e "***** macos/setup.sh - Installing system dependencies only (Python handled by venv)"
    
    # Skip Python installation if using virtual environment
    if [ "$SKIP_PYTHON" -eq 1 ]; then
        echo -e "***** macos/setup.sh - Using virtual environment Python: $PYTHONBIN"
        echo -e "***** macos/setup.sh - Skipping system Python installation"
        
        # Only install essential development tools
        echo -e "    - Install dev tools..."
        cd $BUILD_DIR/resources
        install_devtools
        
        export PATH=$PATH:$BUILD_DIR/bin
    else
        echo -e "***** macos/setup.sh - WARNING: Fallback mode - installing Python from source"
        # ---------------------
        #  INSTALL SYSTEM REQS
        # ---------------------

        # Install proper version of python (fallback mode)
        echo -e "    - Install dev tools..."
        cd $BUILD_DIR/resources
        install_devtools

        echo -e "    - Verify or install Python..."
        if verify_or_install_python; then
            echo -e "      Python setup successful.\n"
        else
            echo -e "      Python setup failed. Exiting.\n"
            exit 1
        fi

        export PATH=$PATH:$BUILD_DIR/bin
    fi

    # --------------------------
    #  INSTALL PYTHON MODULES
    # --------------------------

    # Python packages are handled by venv_manager when using virtual environments
    if [[ "$SKIP_PYTHON" != "1" ]]; then
        echo -e "    - Debug: Before update_py_packages - PYTHONCMD='$PYTHONCMD', PYTHONBIN='$PYTHONBIN'"
        update_py_packages
        local exit_code=$?
    else
        echo -e "    - Skipping Python package installation (handled by venv_manager)"
        local exit_code=0
    fi
    
    # Ensure all required libraries exist for cx_Freeze
    ensure_cx_freeze_libraries
    
    # Append the log separately to avoid pipe issues
    if [ -f $BUILD_DIR/build.log ]; then
        echo "update_py_packages completed with exit code: $exit_code" | sudo tee -a $BUILD_DIR/build.log > /dev/null
    fi

    # Export environment variables for the build process
    export PYTHONCMD
    export PYTHONBIN
    export PYTHONVER
    
    # Export Homebrew variables if they exist
    if [[ -n "$BREWBIN" ]]; then
        export BREWBIN
    fi
    if [[ -n "$HOMEBREW_PREFIX" ]]; then
        export HOMEBREW_PREFIX
        export HOMEBREW_CELLAR="$HOMEBREW_PREFIX/Cellar"
    fi
    
    # Also export PATH with user Python bin directory
    local user_python_bin=$(run_as_user "$PYTHONBIN" -c "import site; import os; print(os.path.join(site.USER_BASE, 'bin'))" 2>/dev/null)
    if [[ -n "$user_python_bin" ]]; then
        export PATH="$user_python_bin:$PATH"
    fi
    
    # Ensure the agent directory has proper permissions for the freeze process
    local original_user=$(get_original_user)
    if [[ $EUID -eq 0 && -n "$SUDO_USER" ]]; then
        echo -e "    - Setting proper permissions for agent directory..."
        sudo chown -R "$original_user" "$AGENT_DIR" 2>/dev/null || true
    fi

    # --------------------------
    #  MISC ADDITIONS
    # --------------------------

}

# Run cx_freeze build with proper permissions
run_freeze_build() {
    echo -e "\n***** macos/setup.sh - run_freeze_build()"
    
    # Clean any existing build directory
    if [[ -d "$AGENT_DIR/build" ]]; then
        rm -rf "$AGENT_DIR/build"
    fi
    
    # Run the freeze process as the original user
    local original_user=$(get_original_user)
    if [[ $EUID -eq 0 && -n "$SUDO_USER" ]]; then
        # Running as root via sudo, run as original user
        echo -e "    - Running freeze as user: $original_user"
        sudo -u "$original_user" -E "$PYTHONBIN" setup.py build_exe
    else
        # Not running as root, run normally
        echo -e "    - Running freeze as current user"
        "$PYTHONBIN" setup.py build_exe
    fi
    
    # Check if build was successful
    if [[ -d "$AGENT_DIR/build" ]]; then
        echo -e "    - Freeze build completed successfully"
        return 0
    else
        echo -e "    - ERROR: Freeze build failed - no build directory created"
        return 1
    fi
}

# Add users/groups
if ! dscl . -read /Users/nagios > /dev/null 2>&1; then
    set +e
    sudo sysadminctl -addUser nagios
    sudo dseditgroup -o create nagios
    sudo dseditgroup -o edit -a nagios -t user nagios
    set -e
fi
