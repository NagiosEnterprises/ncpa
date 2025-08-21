#!/bin/bash

# NCPA Virtual Environment Manager
# This script manages Python virtual environments for NCPA builds across all platforms
# It provides a unified interface for creating, activating, and managing venvs

set -e

# Source version configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/version_config.sh"

# Global configuration
VENV_BASE_DIR="${VENV_BASE_DIR:-$SCRIPT_DIR/venvs}"
VENV_NAME="${VENV_NAME:-ncpa-build}"
VENV_PATH="$VENV_BASE_DIR/$VENV_NAME"
REQUIREMENTS_DIR="$SCRIPT_DIR/resources"
BUILD_LOG="$SCRIPT_DIR/venv_setup.log"

# Platform detection
UNAME=$(uname)
case "$UNAME" in
    "Linux")   PLATFORM="linux" ;;
    "Darwin")  PLATFORM="macos" ;;
    "SunOS"|"Solaris") PLATFORM="solaris" ;;
    "AIX")     PLATFORM="aix" ;;
    *)         PLATFORM="unknown" ;;
esac

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$BUILD_LOG"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "$BUILD_LOG" >&2
}

get_original_user() {
    if [ "$EUID" -eq 0 ]; then
        echo "${SUDO_USER:-$USER}"
    else
        echo "$USER"
    fi
}

run_as_user() {
    local original_user=$(get_original_user)
    if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
        sudo -u "$original_user" "$@"
    else
        "$@"
    fi
}

# Python version detection with preference for configured version
detect_python() {
    local python_candidates=()
    
    # Add configured Python version with highest priority
    if [ -n "$PYTHON_MAJOR_MINOR" ]; then
        python_candidates+=(
            "python$PYTHON_MAJOR_MINOR"
            "/usr/bin/python$PYTHON_MAJOR_MINOR"
            "/usr/local/bin/python$PYTHON_MAJOR_MINOR"
            "/opt/homebrew/bin/python$PYTHON_MAJOR_MINOR"
            "/opt/csw/bin/python$PYTHON_MAJOR_MINOR"
        )
    fi
    
    # Add other common Python versions as fallbacks
    python_candidates+=(
        "python3.13" "python3.12" "python3.11" "python3.10" "python3.9" "python3.8"
        "/usr/bin/python3.13" "/usr/bin/python3.12" "/usr/bin/python3.11"
        "/usr/bin/python3.10" "/usr/bin/python3.9" "/usr/bin/python3.8"
        "/usr/local/bin/python3.13" "/usr/local/bin/python3.12" "/usr/local/bin/python3.11"
        "/usr/local/bin/python3.10" "/usr/local/bin/python3.9" "/usr/local/bin/python3.8"
        "/opt/homebrew/bin/python3.13" "/opt/homebrew/bin/python3.12" "/opt/homebrew/bin/python3.11"
        "/opt/homebrew/bin/python3.10" "/opt/homebrew/bin/python3.9" "/opt/homebrew/bin/python3.8"
        "/opt/csw/bin/python3.13" "/opt/csw/bin/python3.12" "/opt/csw/bin/python3.11"
        "/opt/csw/bin/python3.10" "/opt/csw/bin/python3.9" "/opt/csw/bin/python3.8"
        "python3"
        "/usr/bin/python3"
        "/usr/local/bin/python3"
        "/opt/homebrew/bin/python3"
        "/opt/csw/bin/python3"
    )
    
    log "Detecting Python interpreter (preferred: $PYTHON_MAJOR_MINOR)..."
    

    # Collect all valid Python candidates and their versions (Bash 3.x compatible)
    python_cmds_found=()
    python_versions_found=()
    newest_major=0
    newest_minor=0
    newest_cmd=""
    newest_version=""

    # If no suitable Python found, try to install latest Python with Homebrew on macOS
    if [ "$PLATFORM" = "macos" ]; then
        log "Ensuring latest Python 3 is installed via Homebrew..."
        if command -v brew >/dev/null 2>&1; then
            echo "    - Removing conflicting Homebrew libraries: readline, sqlite, expat..."
            sudo rm -rf /usr/local/opt/readline /usr/local/opt/sqlite /usr/local/opt/expat
            echo "    - Autoremoving Homebrew Python, OpenSSL, and ca-certificates to prevent SSL issues..."
            run_as_user brew uninstall --ignore-dependencies python@3.13 || true
            sudo rm -rf /usr/local/Cellar/python@3.13/
            run_as_user brew uninstall --ignore-dependencies openssl@3 || true
            sudo rm -rf /usr/local/opt/openssl@3
            sudo rm -rf /usr/local/etc/ca-certificates/

            log "Running: brew cleanup"
            run_as_user brew cleanup || true
            # Unset LDFLAGS/CPPFLAGS to avoid linking against missing Homebrew OpenSSL. These will be re-defined later
            unset LDFLAGS
            unset CPPFLAGS
            
            log "Running: brew update"
            if ! run_as_user brew update; then
                error "brew update failed. Please check your Homebrew installation."
                return 1
            fi

            log "Running: brew install --overwrite python"
            if ! run_as_user brew install --overwrite python; then
                error "brew install python failed. Please install Python 3.8+ manually."
                return 1
            fi

            log "Running: brew install --overwrite openssl@3"
            if ! run_as_user brew install --overwrite openssl@3; then
                error "Failed to install openssl@3 via Homebrew."
                return 1
            fi
            log "Running: brew link --overwrite openssl@3"
            if ! run_as_user brew link --overwrite openssl@3; then
                error "Failed to link openssl@3 via Homebrew."
                return 1
            fi

            log "Homebrew Python installation/update complete."
            # Add Homebrew Python to candidates
            python_candidates+=("/opt/homebrew/bin/python3" "/usr/local/bin/python3")
        else
            error "Homebrew not found. Please install Homebrew and Python 3.8+ manually."
        fi
    fi

    for python_cmd in "${python_candidates[@]}"; do
        if command -v "$python_cmd" >/dev/null 2>&1; then
            if version_output=$($python_cmd --version 2>&1); then
                py_version=""
                # Method 1: Extract from "Python X.Y.Z" format
                if [ -z "$py_version" ]; then
                    py_version=$(echo "$version_output" | grep -o 'Python [0-9][0-9]*\.[0-9][0-9]*' | grep -o '[0-9][0-9]*\.[0-9][0-9]*' | head -1)
                fi
                # Method 2: Fallback - extract any X.Y pattern
                if [ -z "$py_version" ]; then
                    py_version=$(echo "$version_output" | grep -o '[0-9][0-9]*\.[0-9][0-9]*' | head -1)
                fi
                # Method 3: Use awk if available
                if [ -z "$py_version" ] && command -v awk >/dev/null 2>&1; then
                    py_version=$(echo "$version_output" | awk '{for(i=1;i<=NF;i++) if($i ~ /^[0-9]+\.[0-9]+/) {split($i,a,"."); print a[1]"."a[2]; break}}')
                fi
                if [ -n "$py_version" ]; then
                    major=$(echo "$py_version" | cut -d. -f1)
                    minor=$(echo "$py_version" | cut -d. -f2)
                    if [ -n "$major" ] && [ -n "$minor" ] && [ "$major" -eq "$major" ] 2>/dev/null && [ "$minor" -eq "$minor" ] 2>/dev/null; then
                        if [ "$major" -gt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -ge 8 ]); then
                            log "Found $python_cmd: version_output='$version_output' -> parsed_version='$py_version' (major=$major, minor=$minor)"
                            python_cmds_found+=("$python_cmd")
                            python_versions_found+=("$py_version")
                            # Track the newest version
                            if [ "$major" -gt "$newest_major" ] || { [ "$major" -eq "$newest_major" ] && [ "$minor" -gt "$newest_minor" ]; }; then
                                newest_major="$major"
                                newest_minor="$minor"
                                newest_cmd="$python_cmd"
                                newest_version="$py_version"
                            fi
                        else
                            log "⚠ Python $py_version at $python_cmd is too old (need >= 3.8)"
                        fi
                    else
                        log "⚠ Failed to parse version for $python_cmd (output: '$version_output', parsed: '$py_version')"
                    fi
                else
                    log "⚠ Could not extract version from $python_cmd output: '$version_output'"
                fi
            else
                log "⚠ Failed to get version from $python_cmd"
            fi
        fi
    done

    # Query the latest available Python version from the package manager
    latest_pkg_version=""
    if [ "$PLATFORM" = "linux" ]; then
        if command -v apt-cache >/dev/null 2>&1; then
            latest_pkg_version=$(apt-cache policy python3 | grep Candidate | awk '{print $2}' | cut -d. -f1,2)
        elif command -v dnf >/dev/null 2>&1; then
            latest_pkg_version=$(dnf info python3 | grep Version | awk '{print $3}' | cut -d. -f1,2)
        elif command -v yum >/dev/null 2>&1; then
            latest_pkg_version=$(yum info python3 | grep Version | awk '{print $3}' | cut -d. -f1,2)
        elif command -v zypper >/dev/null 2>&1; then
            latest_pkg_version=$(zypper info python3 | grep Version | awk '{print $3}' | cut -d. -f1,2)
        fi
    elif [ "$PLATFORM" = "macos" ]; then
        if command -v brew >/dev/null 2>&1; then
            latest_pkg_version=$(brew info python | grep -Eo 'python@[0-9]+\.[0-9]+' | head -1 | grep -Eo '[0-9]+\.[0-9]+')
            if [ -z "$latest_pkg_version" ]; then
                latest_pkg_version=$(brew info python | grep -Eo 'stable [0-9]+\.[0-9]+' | head -1 | grep -Eo '[0-9]+\.[0-9]+')
            fi
        fi
    fi

    # If we could not detect the latest available, fallback to installed
    if [ -z "$latest_pkg_version" ]; then
        latest_pkg_version="$newest_version"
    fi

    latest_major=$(echo "$latest_pkg_version" | cut -d. -f1)
    latest_minor=$(echo "$latest_pkg_version" | cut -d. -f2)

    # Compare installed vs latest available
    if [ "$newest_major" -gt "$latest_major" ] || { [ "$newest_major" -eq "$latest_major" ] && [ "$newest_minor" -ge "$latest_minor" ]; }; then
        # Installed Python is newer or equal to package manager's version
        if [ "$newest_major" -ge 3 ] && [ "$newest_minor" -ge 8 ]; then
            PYTHON_EXECUTABLE="$newest_cmd"
            PYTHON_VERSION="$newest_version"
            log "✓ Using newest installed Python $newest_version: $newest_cmd (newer or equal to package manager $latest_pkg_version)"
            return 0
        else
            error "Newest installed Python ($newest_version) is too old (<3.8)."
            return 1
        fi
    else
        # Installed Python is older than package manager's version
        log "Installed Python ($newest_version) is older than latest available ($latest_pkg_version). Attempting to install/upgrade..."
        if [ "$PLATFORM" = "linux" ]; then
            if command -v apt-get >/dev/null 2>&1; then
                sudo apt-get update && sudo apt-get install -y python3 python3-venv
            elif command -v dnf >/dev/null 2>&1; then
                # Check if python3-venv is available
                if dnf list python3-venv >/dev/null 2>&1; then
                    sudo dnf install -y python3 python3-venv
                else
                    log "python3-venv not available in dnf. Installing python3 only."
                    sudo dnf install -y python3
                fi
            elif command -v yum >/dev/null 2>&1; then
                # Check if python3-venv is available
                if yum list python3-venv >/dev/null 2>&1; then
                    sudo yum install -y python3 python3-venv
                else
                    log "python3-venv not available in yum. Installing python3 only."
                    sudo yum install -y python3
                fi
            elif command -v zypper >/dev/null 2>&1; then
                sudo zypper install -y python3 python3-venv
            else
                error "No supported package manager found for Python installation. Please install Python 3.8+ manually."
                return 1
            fi
        elif [ "$PLATFORM" = "macos" ]; then
            if command -v brew >/dev/null 2>&1; then
                run_as_user brew update
                run_as_user brew install --overwrite python
            else
                error "Homebrew not found. Please install Homebrew and Python 3.8+ manually."
                return 1
            fi
        else
            error "Automatic Python installation not supported for platform: $PLATFORM. Please install Python 3.8+ manually."
            return 1
        fi
        # Re-detect Python after installation
        log "Re-detecting Python after installation..."
        detect_python
        return $?
    fi
    error "No suitable Python 3.8+ interpreter found and automatic installation failed."
    return 1
}

# Create virtual environment
create_venv() {
    log "Creating virtual environment at: $VENV_PATH"
    
    # Detect Python first
    if ! detect_python; then
        return 1
    fi
    
    log "Using Python: $PYTHON_EXECUTABLE (version $PYTHON_VERSION)"
    
    # Remove existing venv if it exists
    if [ -d "$VENV_PATH" ]; then
        log "Removing existing virtual environment..."
        rm -rf "$VENV_PATH"
    fi
    
    # Create directory structure
    mkdir -p "$VENV_BASE_DIR"
    
    # Create the virtual environment
    log "Creating virtual environment with Python $PYTHON_VERSION..."
    if ! "$PYTHON_EXECUTABLE" -m venv "$VENV_PATH"; then
        error "Failed to create virtual environment"
        return 1
    fi
    
    # Verify venv creation
    if [ ! -f "$VENV_PATH/bin/activate" ] && [ ! -f "$VENV_PATH/Scripts/activate" ]; then
        error "Virtual environment creation failed - activate script not found"
        return 1
    fi
    
    log "✓ Virtual environment created successfully"
    return 0
}

# Activate virtual environment and set environment variables
activate_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        error "Virtual environment not found at: $VENV_PATH"
        error "Run: $0 create"
        return 1
    fi
    
    # Determine activation script path (Unix vs Windows)
    if [ -f "$VENV_PATH/bin/activate" ]; then
        ACTIVATE_SCRIPT="$VENV_PATH/bin/activate"
        VENV_PYTHON="$VENV_PATH/bin/python"
        VENV_PIP="$VENV_PATH/bin/pip"
    elif [ -f "$VENV_PATH/Scripts/activate" ]; then
        ACTIVATE_SCRIPT="$VENV_PATH/Scripts/activate"
        VENV_PYTHON="$VENV_PATH/Scripts/python"
        VENV_PIP="$VENV_PATH/Scripts/pip"
    else
        error "Virtual environment activation script not found"
        return 1
    fi
    
    # Source the activation script
    log "Activating virtual environment..."
    source "$ACTIVATE_SCRIPT"
    
    # Export variables for use by other scripts
    export VIRTUAL_ENV="$VENV_PATH"
    export PYTHONBIN="$VENV_PYTHON"
    export PYTHONCMD="$VENV_PYTHON"
    export PYTHON_EXECUTABLE="$VENV_PYTHON"
    export PIP_EXECUTABLE="$VENV_PIP"
    export PATH="$(dirname "$VENV_PYTHON"):$PATH"
    
    # Verify activation
    if ! "$VENV_PYTHON" -c "import sys; assert sys.prefix != sys.base_prefix" 2>/dev/null; then
        error "Virtual environment activation failed"
        return 1
    fi
    
    log "✓ Virtual environment activated"
    log "  Python: $VENV_PYTHON"
    log "  Pip: $VENV_PIP"
    log "  Version: $("$VENV_PYTHON" --version 2>&1)"
    
    return 0
}

# Upgrade pip and install build tools
setup_build_tools() {
    if [ -z "$VIRTUAL_ENV" ]; then
        error "Virtual environment not activated"
        return 1
    fi
    
    log "Setting up build tools in virtual environment..."
    
    # Upgrade pip first
    log "Upgrading pip..."
    if ! "$PIP_EXECUTABLE" install --upgrade pip; then
        error "Failed to upgrade pip"
        return 1
    fi
    
    # Install essential build tools
    log "Installing essential build tools..."
    local build_tools=(
        "setuptools"
        "wheel"
        "build"
    )
    
    for tool in "${build_tools[@]}"; do
        log "Installing $tool..."
        if ! "$PIP_EXECUTABLE" install --upgrade "$tool"; then
            error "Failed to install $tool"
            return 1
        fi
    done
    
    log "✓ Build tools installed successfully"
    return 0
}

# Install Python packages from requirements
install_requirements() {
    if [ -z "$VIRTUAL_ENV" ]; then
        error "Virtual environment not activated"
        return 1
    fi
    
    local req_file="$1"
    if [ -z "$req_file" ]; then
        # Determine platform-specific requirements file
        case "$PLATFORM" in
            "solaris")
                req_file="$REQUIREMENTS_DIR/require-solaris.txt"
                ;;
            *)
                req_file="$REQUIREMENTS_DIR/require.txt"
                ;;
        esac
    fi
    
    if [ ! -f "$req_file" ]; then
        error "Requirements file not found: $req_file"
        return 1
    fi
    
    log "Installing packages from: $req_file"
    
    # Install packages with retry logic
    local max_retries=3
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if "$PIP_EXECUTABLE" install -r "$req_file"; then
            log "✓ Requirements installed successfully"
            return 0
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $max_retries ]; then
                log "Installation failed, retrying ($retry_count/$max_retries)..."
                sleep 2
            fi
        fi
    done
    
    error "Failed to install requirements after $max_retries attempts"
    return 1
}

# Install individual package with fallback strategies
install_package() {
    local package="$1"
    local max_retries=3
    local retry_count=0
    
    if [ -z "$VIRTUAL_ENV" ]; then
        error "Virtual environment not activated"
        return 1
    fi
    
    log "Installing package: $package"
    
    while [ $retry_count -lt $max_retries ]; do
        if "$PIP_EXECUTABLE" install "$package"; then
            log "✓ Package $package installed successfully"
            return 0
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $max_retries ]; then
                log "Package installation failed, retrying ($retry_count/$max_retries)..."
                sleep 2
            fi
        fi
    done
    
    error "Failed to install package $package after $max_retries attempts"
    return 1
}

# List installed packages
list_packages() {
    if [ -z "$VIRTUAL_ENV" ]; then
        error "Virtual environment not activated"
        return 1
    fi
    
    log "Installed packages:"
    "$PIP_EXECUTABLE" list
}

# Clean up virtual environment
clean_venv() {
    if [ -d "$VENV_PATH" ]; then
        log "Removing virtual environment at: $VENV_PATH"
        rm -rf "$VENV_PATH"
        log "✓ Virtual environment removed"
    else
        log "Virtual environment not found at: $VENV_PATH"
    fi
}

# Status check
status() {
    echo "=== NCPA Virtual Environment Status ==="
    echo "Platform: $PLATFORM"
    echo "Virtual Environment Path: $VENV_PATH"
    echo "Requirements Directory: $REQUIREMENTS_DIR"
    echo "Build Log: $BUILD_LOG"
    echo ""
    
    if [ -d "$VENV_PATH" ]; then
        echo "Virtual Environment: ✓ EXISTS"
        if [ -f "$VENV_PATH/bin/python" ]; then
            echo "Python: $("$VENV_PATH/bin/python" --version 2>&1)"
        elif [ -f "$VENV_PATH/Scripts/python.exe" ]; then
            echo "Python: $("$VENV_PATH/Scripts/python.exe" --version 2>&1)"
        fi
        
        # Check if currently activated
        if [ -n "$VIRTUAL_ENV" ] && [ "$VIRTUAL_ENV" = "$VENV_PATH" ]; then
            echo "Status: ✓ ACTIVATED"
            echo "Active Python: $PYTHONBIN"
        else
            echo "Status: ⚠ NOT ACTIVATED"
        fi
    else
        echo "Virtual Environment: ✗ NOT FOUND"
        echo "Status: ✗ NOT CREATED"
    fi
    echo "========================================"
}

# Get activation command for sourcing
get_activation_command() {
    if [ -f "$VENV_PATH/bin/activate" ]; then
        echo "source '$VENV_PATH/bin/activate'"
    elif [ -f "$VENV_PATH/Scripts/activate" ]; then
        echo "source '$VENV_PATH/Scripts/activate'"
    else
        echo "# Virtual environment not found"
        return 1
    fi
}

# Export environment variables for external scripts
# Export environment variables (for display)
export_vars() {
    if [ ! -d "$VENV_PATH" ]; then
        error "Virtual environment not found"
        return 1
    fi
    
    if [ -f "$VENV_PATH/bin/python" ]; then
        export PYTHONBIN="$VENV_PATH/bin/python"
        export PYTHONCMD="$VENV_PATH/bin/python"
        export PIP_EXECUTABLE="$VENV_PATH/bin/pip"
    elif [ -f "$VENV_PATH/Scripts/python.exe" ]; then
        export PYTHONBIN="$VENV_PATH/Scripts/python.exe"
        export PYTHONCMD="$VENV_PATH/Scripts/python.exe"
        export PIP_EXECUTABLE="$VENV_PATH/Scripts/pip.exe"
    else
        error "Python executable not found in virtual environment"
        return 1
    fi
    
    export VIRTUAL_ENV="$VENV_PATH"
    export VENV_PATH="$VENV_PATH"
    export PLATFORM="$PLATFORM"
    
    echo "Exported environment variables:"
    echo "  PYTHONBIN=$PYTHONBIN"
    echo "  PYTHONCMD=$PYTHONCMD"
    echo "  PIP_EXECUTABLE=$PIP_EXECUTABLE"
    echo "  VIRTUAL_ENV=$VIRTUAL_ENV"
    echo "  VENV_PATH=$VENV_PATH"
    echo "  PLATFORM=$PLATFORM"
}

# Generate shell export statements (for eval)
get_env_exports() {
    if [ ! -d "$VENV_PATH" ]; then
        error "Virtual environment not found"
        return 1
    fi
    
    if [ -f "$VENV_PATH/bin/python" ]; then
        echo "export PYTHONBIN=\"$VENV_PATH/bin/python\""
        echo "export PYTHONCMD=\"$VENV_PATH/bin/python\""
        echo "export PIP_EXECUTABLE=\"$VENV_PATH/bin/pip\""
    elif [ -f "$VENV_PATH/Scripts/python.exe" ]; then
        echo "export PYTHONBIN=\"$VENV_PATH/Scripts/python.exe\""
        echo "export PYTHONCMD=\"$VENV_PATH/Scripts/python.exe\""
        echo "export PIP_EXECUTABLE=\"$VENV_PATH/Scripts/pip.exe\""
    else
        error "Python executable not found in virtual environment"
        return 1
    fi
    
    echo "export VIRTUAL_ENV=\"$VENV_PATH\""
    echo "export VENV_PATH=\"$VENV_PATH\""
    echo "export PLATFORM=\"$PLATFORM\""
}

# Usage information
usage() {
    echo "NCPA Virtual Environment Manager"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  create              Create a new virtual environment"
    echo "  activate            Activate the virtual environment"
    echo "  setup               Create venv and install all requirements"
    echo "  install-requirements [file]  Install packages from requirements file"
    echo "  install-package <pkg>        Install a single package"
    echo "  list                List installed packages"
    echo "  status              Show virtual environment status"
    echo "  clean               Remove the virtual environment"
    echo "  export-vars         Show environment variables"
    echo "  get-env-exports     Generate shell export statements for eval"
    echo "  get-activation      Print activation command for sourcing"
    echo ""
    echo "Environment Variables:"
    echo "  VENV_BASE_DIR       Base directory for virtual environments (default: ./venvs)"
    echo "  VENV_NAME           Virtual environment name (default: ncpa-build)"
    echo ""
    echo "Examples:"
    echo "  $0 setup                           # Full setup"
    echo "  source \$($0 get-activation)        # Activate in current shell"
    echo "  $0 install-package requests        # Install single package"
    echo "  VENV_NAME=test $0 create           # Create named environment"
}

# Main command processing
main() {
    local command="$1"
    shift || true
    
    case "$command" in
        "create")
            create_venv
            ;;
        "activate")
            activate_venv
            ;;
        "setup")
            create_venv && activate_venv && setup_build_tools
            ;;
        "install-requirements")
            activate_venv && install_requirements "$1"
            ;;
        "install-package")
            if [ -z "$1" ]; then
                error "Package name required"
                usage
                exit 1
            fi
            activate_venv && install_package "$1"
            ;;
        "list")
            activate_venv && list_packages
            ;;
        "status")
            status
            ;;
        "clean")
            clean_venv
            ;;
        "export-vars")
            export_vars
            ;;
        "get-env-exports")
            get_env_exports
            ;;
        "get-activation")
            get_activation_command
            ;;
        "help"|"--help"|"-h"|"")
            usage
            ;;
        *)
            error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

# Run main function if script is executed directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
