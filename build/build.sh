#!/bin/bash -e

# --------------------------
# Initial setup
# --------------------------


echo -e "***** build/build.sh"

# Source version configuration
BUILD_DIR_FOR_VERSION=$( cd "$(dirname "$0")" ; pwd -P )
source "$BUILD_DIR_FOR_VERSION/version_config.sh"

# User-defined variables
SKIP_SETUP=0
PACKAGE_ONLY=0
BUILD_ONLY=0
BUILD_TRAVIS=0
NO_INTERACTION=0
CLEAN_VENV=0


# --------------------------
# General functions
# --------------------------


usage() {
    echo "Use the build.sh script to setup build environment, compile, "
    echo "and package builds. Works with most common linux OS."
    echo ""
    echo "Example: ./build.sh"
    echo ""
    echo "Options:"
    echo "  -h | --help         Show help/documentation"
    echo "  -S | --skip-setup   Use this option if you have manually set up"
    echo "                      the build environment (don't auto setup)"
    echo "  -p | --package-only Bundle a package only (ncpa folder must exist"
    echo "                      in the build directory)"
    echo "  -b | --build-only   Build the ncpa binaries only (do not package)"
    echo "  -T | --travis       Set up environment for Travis CI builds"
    echo "  -c | --clean        Clean up the build directory"
    echo "  -n | --no-interaction  Run without interactive prompts (auto-confirm)"
    echo "  -C | --clean-venv   Clean virtual environment and recreate"
    echo ""
    echo "Operating Systems Supported:"
    echo " - CentOS, RHEL, Oracle, CloudLinux"
    echo " - Ubuntu, Debian"
    echo " - OpenSUSE, SLES"
    echo " - AIX *"
    echo " - Solaris *"
    echo ""
    echo "* Some systems require extra initial setup, find out more:"
    echo "https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst"
    echo ""
}


clean_build_dir() {
    echo -e "\n***** build/build.sh - Cleaning up build directory..."
    # Remove directories named ncpa-* except for the current version, but do not delete .rpm files
    for dir in "$BUILD_DIR"/ncpa-*; do
        if [ -d "$dir" ]; then
            sudo rm -rf "$dir"
        fi
    done
    sudo rm -rf $AGENT_DIR/build
    sudo rm -rf $BUILD_DIR/NCPA-INSTALL-*
    # sudo rm -f $BUILD_DIR/*.rpm $BUILD_DIR/*.dmg $BUILD_DIR/*.deb
    sudo rm -f $BUILD_DIR/ncpa.spec
    sudo rm -f $BUILD_DIR/*.tar.gz
    sudo rm -rf $BUILD_ROOT
    sudo rm -rf $BUILD_DIR/debbuild
}

# --------------------------
# Startup actions
# --------------------------


# Get the arguments passed to us

while [ -n "$1" ]; do
    case "$1" in
        -h | --help)
            usage
            exit 0
            ;;
        -c | --clean)
            clean_build_dir
            exit 0
            ;;
        -S | --skip-setup)
            SKIP_SETUP=1
            ;;
        -p | --package-only)
            PACKAGE_ONLY=1
            ;;
        -b | --build-only)
            BUILD_ONLY=1
            ;;
        -T | --travis)
            BUILD_TRAVIS=1
            ;;
        -n | --no-interaction)
            NO_INTERACTION=1
            export NO_INTERACTION
            ;;
        -C | --clean-venv)
            CLEAN_VENV=1
            ;;
    esac
    shift
done


# --------------------------
# Virtual Environment Setup
# --------------------------

if [ "$UNAME" == "Darwin" ] || [ "$UNAME" == "AIX" ] || [ "$UNAME" == "SunOS" ]; then
    # For systems without readlink -f, use a simpler, more reliable approach
    echo "=== Path Resolution Debug ==="
    echo "Script invocation (\$0): '$0'"
    echo "Current working directory: $(pwd)"
    
    # Get the directory containing the script
    SCRIPT_DIR="$(dirname "$0")"
    echo "dirname \"\$0\": '$SCRIPT_DIR'"
    
    # Convert to absolute path immediately
    if [ "$SCRIPT_DIR" = "." ]; then
        # Script is in current directory (e.g., ./build.sh)
        BUILD_DIR="$(pwd)"
        echo "Script in current directory, BUILD_DIR: '$BUILD_DIR'"
    elif [ "$SCRIPT_DIR" = ".." ]; then
        # Script is in parent directory (e.g., ../build.sh)
        BUILD_DIR="$(cd .. && pwd)"
        echo "Script in parent directory, BUILD_DIR: '$BUILD_DIR'"
    else
        # Script has a path (e.g., /path/to/build.sh or relative/path/build.sh)
        BUILD_DIR="$(cd "$SCRIPT_DIR" && pwd)"
        echo "Script has path, BUILD_DIR: '$BUILD_DIR'"
    fi
    
    # Handle symlinks if the script itself is a symlink
    SCRIPT_PATH="$0"
    if [ -L "$SCRIPT_PATH" ]; then
        echo "Script is a symlink, resolving..."
        # For symlinks, we need to resolve the actual location
        while [ -L "$SCRIPT_PATH" ]; do
            LINK_TARGET="$(readlink "$SCRIPT_PATH")"
            case "$LINK_TARGET" in
                /*) 
                    # Absolute symlink
                    SCRIPT_PATH="$LINK_TARGET"
                    ;;
                *)
                    # Relative symlink
                    SCRIPT_PATH="$(dirname "$SCRIPT_PATH")/$LINK_TARGET"
                    ;;
            esac
        done
        # Now get the directory of the resolved script
        BUILD_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
        echo "Resolved symlink, final BUILD_DIR: '$BUILD_DIR'"
    fi
    
    # Verify BUILD_DIR is absolute and exists
    case "$BUILD_DIR" in
        /*) 
            if [ -d "$BUILD_DIR" ]; then
                echo "✓ BUILD_DIR is absolute and exists: '$BUILD_DIR'"
            else
                echo "✗ BUILD_DIR is absolute but doesn't exist: '$BUILD_DIR'"
                exit 1
            fi
            ;;
        *)
            echo "✗ BUILD_DIR is not absolute: '$BUILD_DIR'"
            exit 1
            ;;
    esac
    
    AGENT_DIR="$(cd "$BUILD_DIR/../agent" && pwd)"
    echo "Resolved AGENT_DIR: '$AGENT_DIR'"
    echo "====================================="
else
    BUILD_DIR=$(dirname "$(readlink -f "$0")")
    AGENT_DIR=$(readlink -f "$BUILD_DIR/../agent")
fi
NCPA_VER=$(cat $BUILD_DIR/../VERSION)

echo "=== Path Resolution Debug ==="
echo "Script invocation: $0"
echo "Script location: $(dirname "$0")"
echo "BUILD_DIR (absolute): $BUILD_DIR"
echo "AGENT_DIR (absolute): $AGENT_DIR"
echo "UNAME: $UNAME"
echo "Current working directory: $(pwd)"
echo "============================="

# Virtual environment configuration
VENV_MANAGER="$BUILD_DIR/venv_manager.sh"
VENV_NAME="ncpa-build-$(echo "$UNAME" | tr '[:upper:]' '[:lower:]')"
export VENV_NAME

setup_virtual_environment() {
    echo "=== Setting up Virtual Environment ==="
    # Clean venv if requested
    if [ $CLEAN_VENV -eq 1 ]; then
        echo "Cleaning existing virtual environment..."
        if [ -x "$VENV_MANAGER" ]; then
            "$VENV_MANAGER" clean
        fi
    fi
    # Check if venv manager exists
    if [ ! -x "$VENV_MANAGER" ]; then
        echo "ERROR: Virtual environment manager not found or not executable: $VENV_MANAGER"
        exit 1
    fi
    # Setup virtual environment
    echo "Creating and setting up virtual environment: $VENV_NAME"
    if ! "$VENV_MANAGER" setup; then
        echo "ERROR: Failed to setup virtual environment"
        exit 1
    fi
    # Export environment variables from venv manager
    echo "Configuring environment variables..."
    eval "$("$VENV_MANAGER" get-env-exports)"
    # Verify venv is working
    if [ -z "$PYTHONBIN" ] || [ ! -x "$PYTHONBIN" ]; then
        echo "ERROR: Python executable not found after venv setup: $PYTHONBIN"
        exit 1
    fi
    echo "✓ Virtual environment ready"
    echo "  Python: $PYTHONBIN"
    echo "  Version: $($PYTHONBIN --version 2>&1)"
    echo "  Virtual Env: $VIRTUAL_ENV"
    echo "=================================="

    # Explicit SSL check
    echo "Checking Python SSL support..."
    if ! "$PYTHONBIN" -c "import ssl; print(ssl.OPENSSL_VERSION)" 2>/dev/null; then
        echo "WARNING: Python SSL module is not available. Some features may not work."
    else
        echo "✓ Python SSL module is available."
        echo "Python SSL version: $($PYTHONBIN -c 'import ssl; print(ssl.OPENSSL_VERSION)')"
    fi
}


# --------------------------
# Do initial setup
# --------------------------


# Load required things for different systems
echo -e "\nRunning build for: $UNAME"


# Always setup virtual environment first
setup_virtual_environment

# Export all relevant environment variables for subshells
echo "Exporting:"
echo "PYTHONBIN: $PYTHONBIN"
echo "VIRTUAL_ENV: $VIRTUAL_ENV"
echo "VENV_NAME: $VENV_NAME"
echo "BUILD_DIR: $BUILD_DIR"
echo "AGENT_DIR: $AGENT_DIR"
export PYTHONBIN
export VIRTUAL_ENV
export VENV_NAME
export BUILD_DIR
export AGENT_DIR

# Load platform-specific configurations (but skip their Python setup)
export SKIP_PYTHON=1  # Tell platform scripts to skip Python installation

if [ "$UNAME" == "Linux" ]; then
    export PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:/root/bin:$PATH
    . $BUILD_DIR/linux/setup.sh
elif [ "$UNAME" == "SunOS" ] || [ "$UNAME" == "Solaris" ]; then
    . $BUILD_DIR/solaris/setup.sh
elif [ "$UNAME" == "AIX" ]; then
    . $BUILD_DIR/aix/setup.sh
elif [ "$UNAME" == "Darwin" ]; then
    . $BUILD_DIR/macos/setup.sh
    # Restore PYTHONBIN after macOS setup script, in case it was lost
    eval "$($VENV_MANAGER get-env-exports)"
    export PYTHONBIN
else
    echo "Not a supported system for our build script."
    echo "If you're sure all pre-reqs are installed, try running the"
    echo "build without setup: ./build.sh --build-only"
fi

# Always source any *_build_env.sh files for compiler environment
for env_file in /tmp/*_build_env.sh; do
    if [ -f "$env_file" ]; then
        echo "Sourcing $env_file for compiler environment..."
        source "$env_file"
    fi
done

# Check that pre-reqs have been installed
if [ $BUILD_TRAVIS -eq 0 ] && [ $PACKAGE_ONLY -eq 0 ] && [ $BUILD_ONLY -eq 0 ]; then
    # With venv approach, we always have Python available
    if [ $SKIP_SETUP -eq 0 ] && [ ! -f $BUILD_DIR/prereqs.installed ]; then
        echo "** WARNING: This should not be done on a production system. **"
        if [ $NO_INTERACTION -eq 1 ] || { read -r -p "Automatically install system pre-reqs? [Y/n] " resp && [[ $resp =~ ^(yes|y|Y| ) ]] || [[ -z $resp ]]; }; then
            install_prereqs
            sudo touch $BUILD_DIR/prereqs.installed
        fi
    fi

elif [ $BUILD_TRAVIS -eq 1 ]; then
    # Set up travis environment
    sudo useradd -s /sbin/nologin nagios
    cd $BUILD_DIR
    
    # Use virtual environment if available, otherwise fall back to system pip
    if [[ -n "$VENV_MANAGER" && -f "$VENV_MANAGER" ]]; then
        echo "Setting up virtual environment for Travis CI build..."
        if ! "$VENV_MANAGER" setup; then
            echo "Virtual environment setup failed, falling back to system pip"
            python -m pip install -r resources/require.txt --upgrade
        fi
    else
        echo "Using system pip for Travis CI build..."
        python -m pip install -r resources/require.txt --upgrade
    fi
    exit 0
fi


# Update the required python modules !!! update_py_packages() Already run in install_prereqs()
cd $BUILD_DIR
# echo "Updating python modules..."
# update_py_packages >> $BUILD_DIR/build.log


# --------------------------
# Build
# --------------------------


# Clean build dir
clean_build_dir


# Build the python with cx_Freeze
cd $BUILD_DIR
find $AGENT_DIR -name *.pyc -exec rm '{}' \;
sudo mkdir -p $AGENT_DIR/plugins
sudo mkdir -p $AGENT_DIR/build
sudo mkdir -p $AGENT_DIR/var/log
# cat /dev/null > $AGENT_DIR/var/log/ncpa_passive.log
# cat /dev/null > $AGENT_DIR/var/log/ncpa_listener.log

# Add file with current GIT hash to build
GIT_LONG="Not built under GIT"
GIT_HASH_FILE="NoGIT.githash"

if command -v git > /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Git repository detected, extracting version information..."
    GIT_LONG=$(git rev-parse HEAD 2>/dev/null || echo "Unable to get git hash")
    GIT_SHORT=$(git rev-parse --short HEAD 2>/dev/null || echo "nogit")
    GIT_UNCOMMITTED=$(git status --untracked-files=no --porcelain 2>/dev/null || echo "")
    # echo "GIT_UNCOMMITTED: $GIT_UNCOMMITTED"
    if [ "$GIT_UNCOMMITTED" ]; then
        GIT_LONG="$GIT_LONG++  compiled with uncommitted changes"
        GIT_SHORT="$GIT_SHORT++"
    fi
    GIT_HASH_FILE="git-$GIT_SHORT.githash"
    # echo "GIT_LONG: $GIT_LONG"
    # echo "GIT_SHORT: $GIT_SHORT"
    echo "GIT_HASH_FILE: $GIT_HASH_FILE"
else
    echo "No git repository found or git not available, using default version info"
fi

echo "PYTHONBIN before Building Binaries Subshell"
echo "PYTHONBIN: $PYTHONBIN"
(
    # On macOS, explicitly export PYTHONBIN to subshell to avoid losing it
    if [ "$UNAME" == "Darwin" ]; then
        export PYTHONBIN
    fi
    echo -e "\nBuilding NCPA binaries..."
    echo "=== Subshell Environment Debug ==="
    BUILD_DIR=$(pwd)
    echo "BUILD_DIR at start of subshell: $BUILD_DIR"
    echo "AGENT_DIR at start of subshell: $AGENT_DIR"
    echo "Current directory at start of subshell: $(pwd)"
    echo "=================================="
    cd $AGENT_DIR

    echo -e "\nFreezing app (may take a minute)..."
    # Set environment variables to help with Solaris build issues
    if [ "$UNAME" == "SunOS" ]; then
        echo "Setting Solaris-specific environment variables for cx_Freeze..."
        export CX_FREEZE_SILENCE_MISSING_MODULES=1
        export SOLARIS_BUILD=1
        
        # CRITICAL: Set up C++ compiler environment for Python package compilation
        echo "=== Setting up C++ compiler environment for Python builds ==="
        
        # Source the compiler setup if available
        if [ -f "$BUILD_DIR/solaris/setup_compiler.sh" ]; then
            echo "Loading Solaris compiler setup..."
            source "$BUILD_DIR/solaris/setup_compiler.sh"
        elif [ -f "/tmp/solaris_build_env.sh" ]; then
            echo "Loading build environment from setup..."
            source "/tmp/solaris_build_env.sh"
        else
            echo "Setting up compiler environment inline..."
            
            # Try to find working compilers
            cpp_compiler=""
            c_compiler=""
            
            # Search for C++ compilers (prefer newer versions)
            for cxx_candidate in g++-14 g++-13 g++-12 g++-11 g++-10 g++-9 g++-8 g++-7 /usr/gcc/*/bin/g++ /usr/local/bin/g++* /opt/csw/bin/g++* g++; do
                if command -v "$cxx_candidate" >/dev/null 2>&1; then
                    # Test if this compiler works
                    if echo 'int main(){return 0;}' | "$cxx_candidate" -x c++ - -o /tmp/test_cxx_build_$$ 2>/dev/null; then
                        rm -f /tmp/test_cxx_build_$$
                        echo "✓ Found working C++ compiler: $cxx_candidate"
                        cpp_compiler="$cxx_candidate"
                        
                        # Find corresponding C compiler
                        cxx_dir=$(dirname "$cxx_candidate" 2>/dev/null || echo "/usr/bin")
                        cxx_base=$(basename "$cxx_candidate")
                        
                        # Try to find matching C compiler
                        case "$cxx_base" in
                            g++-*)
                                version_suffix="${cxx_base#g++-}"
                                gcc_candidate="gcc-$version_suffix"
                                ;;
                            g++)
                                gcc_candidate="gcc"
                                ;;
                            *)
                                gcc_candidate="gcc"
                                ;;
                        esac
                        
                        # Look for C compiler in same directory first, then in PATH
                        for gcc_path in "$cxx_dir/$gcc_candidate" "$(which $gcc_candidate 2>/dev/null)" "gcc"; do
                            if [ -n "$gcc_path" ] && command -v "$gcc_path" >/dev/null 2>&1; then
                                if echo 'int main(){return 0;}' | "$gcc_path" -x c - -o /tmp/test_cc_build_$$ 2>/dev/null; then
                                    rm -f /tmp/test_cc_build_$$
                                    echo "✓ Found working C compiler: $gcc_path"
                                    c_compiler="$gcc_path"
                                    break
                                fi
                            fi
                        done
                        
                        if [ -n "$c_compiler" ]; then
                            break  # Found both compilers
                        fi
                    fi
                fi
            done
            
            # Set up the environment if compilers were found
            if [ -n "$cpp_compiler" ] && [ -n "$c_compiler" ]; then
                echo "✓ Setting up compiler environment:"
                echo "  CC=$c_compiler"
                echo "  CXX=$cpp_compiler"
                
                export CC="$c_compiler"
                export CXX="$cpp_compiler"
                export CFLAGS="-fPIC"
                export CXXFLAGS="-fPIC -std=c++11"
                export LDFLAGS=""
                
                # Make sure the compiler directory is in PATH
                cpp_dir=$(dirname "$cpp_compiler")
                if [ -n "$cpp_dir" ] && [ "$cpp_dir" != "/usr/bin" ]; then
                    export PATH="$cpp_dir:$PATH"
                fi
                
                echo "✓ C++ compiler environment configured for Python builds"
            else
                echo "⚠ WARNING: No working C/C++ compilers found"
                echo "⚠ Python packages requiring compilation (like greenlet) may fail"
                echo "⚠ Attempting to set basic fallback environment..."
                
                # Set fallback environment
                export CC="gcc"
                export CXX="g++"
                export CFLAGS="-fPIC"
                export CXXFLAGS="-fPIC -std=c++11"
                export LDFLAGS=""
            fi
        fi
        
        # Display final compiler environment
        echo "Final compiler environment:"
        echo "  CC=$CC"
        echo "  CXX=$CXX"
        echo "  CFLAGS=$CFLAGS"
        echo "  CXXFLAGS=$CXXFLAGS"
        echo "  PATH (first 3 entries): $(echo "$PATH" | cut -d: -f1-3)"
        echo "=== End compiler setup ==="
        echo ""
        
        # Ensure patchelf is available for cx_Freeze
        echo "Ensuring patchelf wrapper is properly configured..."
        
        # Force virtual environment bin directory to be first in PATH
        if [ -n "$VIRTUAL_ENV" ] && [ -d "$VIRTUAL_ENV/bin" ]; then
            export PATH="$VIRTUAL_ENV/bin:$PATH"
            echo "Updated PATH to prioritize virtual environment: $VIRTUAL_ENV/bin"
        fi
        
        # Ensure /usr/local/bin is in PATH
        if ! echo "$PATH" | grep -q "/usr/local/bin"; then
            export PATH="/usr/local/bin:$PATH"
            echo "Added /usr/local/bin to PATH"
        fi
        
        # ALWAYS ensure patchelf wrapper is available in virtual environment
        echo "Ensuring patchelf wrapper is available in virtual environment..."
        
        # Always copy the wrapper if it exists in /usr/local/bin, regardless of current patchelf status
        if [ -f "/usr/local/bin/patchelf" ] && [ -n "$VIRTUAL_ENV" ] && [ -d "$VIRTUAL_ENV/bin" ]; then
            # Check if the file already exists in venv and is identical
            if [ -f "$VIRTUAL_ENV/bin/patchelf" ]; then
                if cmp -s "/usr/local/bin/patchelf" "$VIRTUAL_ENV/bin/patchelf" 2>/dev/null; then
                    echo "✓ Patchelf wrapper already exists and is identical in virtual environment"
                else
                    echo "Updating patchelf wrapper in virtual environment (files differ)..."
                    cp /usr/local/bin/patchelf "$VIRTUAL_ENV/bin/patchelf"
                    chmod +x "$VIRTUAL_ENV/bin/patchelf"
                    echo "✓ Patchelf wrapper updated in: $VIRTUAL_ENV/bin/patchelf"
                fi
            else
                echo "Copying patchelf wrapper from /usr/local/bin to virtual environment..."
                cp /usr/local/bin/patchelf "$VIRTUAL_ENV/bin/patchelf"
                chmod +x "$VIRTUAL_ENV/bin/patchelf"
                echo "✓ Patchelf wrapper copied to: $VIRTUAL_ENV/bin/patchelf"
            fi
        fi
        
        # CRITICAL: Ensure virtual environment bin is FIRST in PATH
        if [ -n "$VIRTUAL_ENV" ] && [ -d "$VIRTUAL_ENV/bin" ]; then
            # Remove any existing venv paths from PATH to avoid duplicates
            PATH_WITHOUT_VENV=$(echo "$PATH" | sed "s|$VIRTUAL_ENV/bin:||g" | sed "s|:$VIRTUAL_ENV/bin||g" | sed "s|$VIRTUAL_ENV/bin$||g")
            export PATH="$VIRTUAL_ENV/bin:$PATH_WITHOUT_VENV"
            echo "✓ Virtual environment bin directory prioritized in PATH"
            echo "PATH (first 3 entries): $(echo "$PATH" | cut -d: -f1-3)"
        fi
        
        # Clear command hash to ensure fresh lookups
        hash -r
        
        if command -v patchelf >/dev/null 2>&1; then
            patchelf_path=$(which patchelf)
            echo "patchelf found at $patchelf_path"
            
            patchelf_version=$(patchelf --version 2>&1 || echo 'version check failed')
            echo "patchelf version: $patchelf_version"
            
            # Check if it's our wrapper
            if echo "$patchelf_version" | grep -q "wrapper"; then
                echo "✓ Using our Solaris-compatible patchelf wrapper"
            else
                echo "⚠ Warning: patchelf may not be our wrapper - this could cause issues"
                echo "Attempting to ensure wrapper is used..."
                
                # Try to force our wrapper to take precedence
                if [ -f "/usr/local/bin/patchelf" ]; then
                    # Check if /usr/local/bin/patchelf is our wrapper
                    if head -1 /usr/local/bin/patchelf 2>/dev/null | grep -q "#!/bin/bash" && grep -q "wrapper" /usr/local/bin/patchelf 2>/dev/null; then
                        echo "Found our wrapper at /usr/local/bin/patchelf"
                        if [ -n "$VIRTUAL_ENV" ] && [ -d "$VIRTUAL_ENV/bin" ]; then
                            echo "Copying wrapper to virtual environment..."
                            cp /usr/local/bin/patchelf "$VIRTUAL_ENV/bin/patchelf"
                            chmod +x "$VIRTUAL_ENV/bin/patchelf"
                            export PATH="$VIRTUAL_ENV/bin:$PATH"
                            hash -r
                            echo "Updated patchelf location: $(which patchelf)"
                        fi
                    fi
                fi
            fi
            
            # Test patchelf functionality on a simple binary first
            echo "Testing patchelf functionality..."
            test_binary="/bin/ls"
            if [ -f "$test_binary" ]; then
                echo "Testing patchelf --print-rpath on $test_binary:"
                patchelf --print-rpath "$test_binary" 2>&1 || echo "rpath test failed"
                echo "Testing patchelf --print-needed on $test_binary:"
                patchelf --print-needed "$test_binary" 2>&1 || echo "needed test failed"
            fi
        else
            echo "WARNING: patchelf not found - cx_Freeze may fail"
        fi
        
        # Set additional environment variables to help cx_Freeze handle patchelf failures gracefully
        export CX_FREEZE_IGNORE_RPATH_ERRORS=1
        export CX_FREEZE_FALLBACK_MODE=1
        
        # CRITICAL: Ensure our patchelf wrapper is active right before cx_Freeze runs
        echo "Final patchelf verification before cx_Freeze..."
        if command -v patchelf >/dev/null 2>&1; then
            current_patchelf=$(which patchelf)
            echo "Current patchelf location: $current_patchelf"
            
            # Test the version to see if it's our wrapper
            version_output=$(patchelf --version 2>&1)
            echo "patchelf version output: $version_output"
            
            if echo "$version_output" | grep -q "wrapper"; then
                echo "✓ Our wrapper is active - cx_Freeze should work"
            else
                echo "⚠ WARNING: patchelf is not our wrapper - FORCING emergency replacement"
                
                # FORCE replacement: directly overwrite ALL patchelf binaries with our wrapper
                echo "Emergency: Forcefully replacing ALL patchelf binaries with wrapper"
                
                # Create emergency wrapper content
                emergency_wrapper_content='#!/bin/bash
# Emergency patchelf wrapper for Solaris cx_Freeze compatibility
case "$1" in
    "--version") echo "patchelf 0.18.0 (emergency-wrapper)"; exit 0 ;;
    "--print-rpath") 
        if [ -n "$2" ] && [ -f "$2" ]; then
            if command -v readelf >/dev/null 2>&1; then
                readelf -d "$2" 2>/dev/null | grep -E "RPATH|RUNPATH" | sed "s/.*\[\(.*\)\]/\1/" | head -1
            else
                echo ""
            fi
        else
            echo ""
        fi
        exit 0 ;;
    "--set-rpath"|"--add-rpath"|"--remove-rpath"|"--set-interpreter"|"--shrink-rpath"|"--add-needed"|"--remove-needed"|"--replace-needed"|"--no-default-lib")
        echo "INFO: patchelf emergency wrapper handling: $@" >&2
        exit 0 ;;
    "--print-needed")
        if [ -n "$2" ] && [ -f "$2" ]; then
            if command -v readelf >/dev/null 2>&1; then
                readelf -d "$2" 2>/dev/null | grep NEEDED | sed "s/.*\[\(.*\)\]/\1/"
            elif command -v ldd >/dev/null 2>&1; then
                ldd "$2" 2>/dev/null | awk "{print \$1}" | grep -v "=>"
            fi
        fi
        exit 0 ;;
    "--print-interpreter")
        if [ -n "$2" ] && [ -f "$2" ]; then
            if command -v readelf >/dev/null 2>&1; then
                readelf -l "$2" 2>/dev/null | grep interpreter | sed "s/.*: \(.*\)\]/\1/"
            fi
        fi
        exit 0 ;;
    *) exit 0 ;;
esac'
                
                # Force replacement of the current patchelf binary
                echo "Backing up and replacing: $current_patchelf"
                sudo cp "$current_patchelf" "${current_patchelf}.original-backup" 2>/dev/null || true
                echo "$emergency_wrapper_content" | sudo tee "$current_patchelf" > /dev/null
                sudo chmod +x "$current_patchelf"
                
                # Also replace common locations where patchelf might be found
                force_replace_locations=(
                    "/usr/local/bin/patchelf"
                    "$VIRTUAL_ENV/bin/patchelf"
                    "/root/.local/bin/patchelf"
                )
                
                for location in "${force_replace_locations[@]}"; do
                    if [ -n "$location" ] && [ "$location" != "$current_patchelf" ]; then
                        echo "Also replacing: $location"
                        sudo mkdir -p "$(dirname "$location")" 2>/dev/null || true
                        echo "$emergency_wrapper_content" | sudo tee "$location" > /dev/null
                        sudo chmod +x "$location" 2>/dev/null
                    fi
                done
                
                # Clear command cache and verify
                hash -r
                sleep 1  # Give the system a moment
                
                echo "Emergency wrapper installed. Testing..."
                new_version=$(patchelf --version 2>&1)
                echo "New patchelf version: $new_version"
                
                if echo "$new_version" | grep -q "emergency-wrapper"; then
                    echo "✓ Emergency wrapper is now active"
                else
                    echo "✗ Emergency wrapper installation failed - build will likely fail"
                    echo "Current patchelf path: $(which patchelf)"
                    echo "File exists check: $(ls -la $(which patchelf) 2>/dev/null || echo 'not found')"
                fi
            fi
        else
            echo "✗ CRITICAL: patchelf not found at all - cx_Freeze will fail"
        fi
        
        # FINAL: Verify patchelf is available right before cx_Freeze
        echo "=== FINAL PATCHELF VERIFICATION ==="
        echo "Current PATH (first 5 entries): $(echo "$PATH" | cut -d: -f1-5)"
        echo "VIRTUAL_ENV: $VIRTUAL_ENV"
        
        if command -v patchelf >/dev/null 2>&1; then
            patchelf_location=$(which patchelf)
            echo "✓ patchelf found at: $patchelf_location"
            
            # Test patchelf version
            patchelf_version=$(patchelf --version 2>&1 || echo "version check failed")
            echo "patchelf version: $patchelf_version"
            
            # Verify it's executable
            if [ -x "$patchelf_location" ]; then
                echo "✓ patchelf is executable"
            else
                echo "✗ patchelf is not executable"
            fi
        else
            echo "✗ CRITICAL: patchelf not found in PATH"
            echo "Available commands in first PATH directory:"
            first_path_dir=$(echo "$PATH" | cut -d: -f1)
            if [ -d "$first_path_dir" ]; then
                ls -la "$first_path_dir" | grep patchelf || echo "No patchelf found"
            fi
            
            # Emergency installation if needed
            if [ -f "/usr/local/bin/patchelf" ]; then
                echo "Emergency: Creating direct symlink to system patchelf wrapper"
                ln -sf /usr/local/bin/patchelf /usr/bin/patchelf 2>/dev/null || true
                hash -r
            fi
        fi
        echo "==================================="
        
        # Run the build
        echo "Starting cx_Freeze build with enhanced error handling..."
        $PYTHONBIN setup.py build_exe 2>&1 | sudo tee $BUILD_DIR/build.log
        BUILD_RESULT=$?
        
        # Check if build failed
        if [ $BUILD_RESULT -ne 0 ]; then
            echo "cx_Freeze build failed on Solaris with exit code: $BUILD_RESULT"
            echo "Checking for partial build artifacts..."
            if [ -d "$AGENT_DIR/build" ]; then
                echo "Build directory contents:"
                ls -la "$AGENT_DIR/build/"
                # Look for any exe.* directories that might have been created
                exe_dirs=$(find "$AGENT_DIR/build" -type d -name "exe.*" 2>/dev/null)
                if [ -n "$exe_dirs" ]; then
                    echo "Found partial build directories:"
                    echo "$exe_dirs"
                    echo "Contents of first partial build:"
                    ls -la $(echo "$exe_dirs" | head -1) 2>/dev/null || echo "Could not list contents"
                fi
            fi
            echo "Last 50 lines of build log:"
            tail -50 "$BUILD_DIR/build.log" 2>/dev/null || echo "Could not read build log"
            exit $BUILD_RESULT
        fi
    else

        # CRITICAL: Ensure virtual environment bin is FIRST in PATH
        if [ -n "$VIRTUAL_ENV" ] && [ -d "$VIRTUAL_ENV/bin" ]; then
            # Remove any existing venv paths from PATH to avoid duplicates
            PATH_WITHOUT_VENV=$(echo "$PATH" | sed "s|$VIRTUAL_ENV/bin:||g" | sed "s|:$VIRTUAL_ENV/bin||g" | sed "s|$VIRTUAL_ENV/bin$||g")
            export PATH="$VIRTUAL_ENV/bin:$PATH_WITHOUT_VENV"
            echo "✓ Virtual environment bin directory prioritized in PATH"
            echo "PATH (first 3 entries): $(echo "$PATH" | cut -d: -f1-3)"
        fi

        # Clear command hash to ensure fresh lookups
        hash -r

        # Run the build
        echo "Attempting to build cx_Freeze..."
        echo "Python binary: $PYTHONBIN"
        $PYTHONBIN setup.py build_exe | sudo tee $BUILD_DIR/build.log
    fi


    echo -e "\nSet up packaging dirs..."
    # Copy the cx_Freeze build output to BUILD_DIR
    echo "=== Directory Setup Debug ==="
    echo "BUILD_DIR variable content: '$BUILD_DIR'"
    echo "BUILD_DIR variable length: ${#BUILD_DIR}"
    echo "BUILD_DIR starts with '/': $([ "${BUILD_DIR:0:1}" = "/" ] && echo "YES" || echo "NO")"
    echo "Current directory: $(pwd)"
    echo "BUILD_DIR: $BUILD_DIR"
    echo "AGENT_DIR: $AGENT_DIR"
    echo "=========================="
    
    # Find the cx_Freeze build directory (it varies by platform)
    echo "Looking for cx_Freeze build directory in: $AGENT_DIR/build"
    if [ "$UNAME" == "SunOS" ]; then
        # Solaris find doesn't support -maxdepth, use alternative approach
        BUILD_EXE_DIR=$(find "$AGENT_DIR/build" -type d -name "exe.*" | head -1)
    else
        BUILD_EXE_DIR=$(find "$AGENT_DIR/build" -maxdepth 1 -name "exe.*" -type d | head -1)
    fi
    
    if [ -z "$BUILD_EXE_DIR" ]; then
        echo "ERROR: Could not find cx_Freeze build directory in $AGENT_DIR/build/"
        echo "Available directories:"
        ls -la "$AGENT_DIR/build/" 2>/dev/null || echo "Build directory does not exist"
        echo "Platform: $UNAME"
        echo "Python version: $($PYTHONBIN --version 2>&1 || echo 'Python version check failed')"
        echo "cx_Freeze may have failed. Check the build log above for errors."
        
        # Show the last part of the build log for debugging
        if [ -f "$BUILD_DIR/build.log" ]; then
            echo "Last 30 lines of build log:"
            tail -30 "$BUILD_DIR/build.log"
        fi
        exit 1
    fi
    
    echo "Found cx_Freeze build directory: $BUILD_EXE_DIR"
    
    # Verify the build directory has the expected structure
    echo "Verifying build directory structure..."
    if [ ! -f "$BUILD_EXE_DIR/ncpa" ]; then
        echo "WARNING: Main ncpa executable not found in $BUILD_EXE_DIR"
        echo "Contents of build directory:"
        ls -la "$BUILD_EXE_DIR" 2>/dev/null
    else
        echo "✓ Main ncpa executable found"
    fi
    
    # Copy the build directory to BUILD_DIR/ncpa (rename the exe.* directory to ncpa)
    echo "=== Copy Operation ==="
    echo "Current directory: $(pwd)"
    echo "Copying $BUILD_EXE_DIR to $BUILD_DIR/ncpa"
    
    # Remove any existing ncpa directory in BUILD_DIR
    if [ -d "$BUILD_DIR/ncpa" ]; then
        echo "Removing existing $BUILD_DIR/ncpa directory"
        sudo rm -rf "$BUILD_DIR/ncpa"
    fi
    
    # Copy the build directory (original working approach from venv implementation)
    if [ "$UNAME" == "Darwin" ]; then
        # On macOS, use -L to follow symbolic links to avoid issues with relative paths
        echo "Copying macOS build with symbolic link resolution..."
        sudo cp -RLf "$BUILD_EXE_DIR" $BUILD_DIR/ncpa
    elif [ "$UNAME" == "SunOS" ]; then
        # On Solaris, ensure consistent directory copying behavior
        echo "Copying Solaris build..."
        # First, ensure the parent directory exists
        sudo mkdir -p "$BUILD_DIR"
        
        # Add diagnostic information
        echo "=== Solaris Copy Diagnostics ==="
        echo "Source: $BUILD_EXE_DIR"
        echo "Destination: $BUILD_DIR/ncpa"
        echo "Source exists: $([ -d "$BUILD_EXE_DIR" ] && echo "YES" || echo "NO")"
        echo "Source contents:"
        ls -la "$BUILD_EXE_DIR" 2>/dev/null || echo "Cannot list source directory"
        echo "Destination parent exists: $([ -d "$BUILD_DIR" ] && echo "YES" || echo "NO")"
        echo "================================"
        
        # Copy the directory and rename it to ncpa (same as Linux approach)
        if command -v gcp >/dev/null 2>&1; then
            # Use GNU cp if available - copy directory itself, not contents
            echo "Using GNU cp (gcp) for Solaris copy..."
            if sudo gcp -rf "$BUILD_EXE_DIR" "$BUILD_DIR/ncpa"; then
                echo "✓ GNU cp succeeded"
            else
                echo "✗ GNU cp failed with exit code: $?"
                exit 1
            fi
        else
            # Use standard Solaris cp - copy directory itself, not contents
            echo "Using standard Solaris cp..."
            if sudo cp -rf "$BUILD_EXE_DIR" "$BUILD_DIR/ncpa"; then
                echo "✓ Standard cp succeeded"
            else
                echo "✗ Standard cp failed with exit code: $?"
                exit 1
            fi
        fi
        
        # Verify the copy worked
        echo "=== Solaris Copy Verification ==="
        echo "Destination exists: $([ -d "$BUILD_DIR/ncpa" ] && echo "YES" || echo "NO")"
        if [ -d "$BUILD_DIR/ncpa" ]; then
            echo "Destination contents:"
            ls -la "$BUILD_DIR/ncpa" | head -10
            echo "Main executable exists: $([ -f "$BUILD_DIR/ncpa/ncpa" ] && echo "YES" || echo "NO")"
            
            # Check if we accidentally created a nested structure
            if ls -1 "$BUILD_DIR/ncpa/" 2>/dev/null | grep -q "^exe\."; then
                echo "WARNING: Found nested exe.* directory structure!"
                echo "Nested directories found:"
                ls -la "$BUILD_DIR/ncpa/" | grep "^d" | grep "exe\."
                echo "This indicates the copy created a nested structure instead of renaming."
                echo "Attempting to fix by moving contents up one level..."
                
                # Find the nested exe.* directory (Solaris-compatible approach)
                nested_dir=""
                for dir in "$BUILD_DIR/ncpa"/exe.*; do
                    if [ -d "$dir" ]; then
                        nested_dir="$dir"
                        break
                    fi
                done
                
                if [ -n "$nested_dir" ]; then
                    echo "Moving contents from $nested_dir to $BUILD_DIR/ncpa"
                    # Create a temporary directory
                    temp_dir="$BUILD_DIR/ncpa_temp_$$"
                    sudo mv "$nested_dir" "$temp_dir"
                    sudo rm -rf "$BUILD_DIR/ncpa"
                    sudo mv "$temp_dir" "$BUILD_DIR/ncpa"
                    echo "✓ Fixed nested directory structure"
                fi
            fi
        fi
        echo "Final verification:"
        echo "ncpa directory exists: $([ -d "$BUILD_DIR/ncpa" ] && echo "YES" || echo "NO")"
        echo "ncpa executable exists: $([ -f "$BUILD_DIR/ncpa/ncpa" ] && echo "YES" || echo "NO")"
        echo "================================="
    else
        # On other systems (Linux, AIX), use standard recursive copy
        echo "Copying build for $UNAME..."
        sudo cp -rf "$BUILD_EXE_DIR" $BUILD_DIR/ncpa
    fi
    
    echo $GIT_LONG | sudo tee $BUILD_DIR/ncpa/$GIT_HASH_FILE

    # REMOVE LIBFFI COPY - PLEASE CHANGE THIS LATER
    # It should be in .libs_cffi_backend for proper linking and
    # possibly in the future we will fix this but we have to include
    # the exact version ... this will delete the duplicate which should
    # have a special name like libffi-6322464e.so.6.0.4
    sudo rm -f $BUILD_DIR/ncpa/libffi-*.so.*

    # Handle problematic symlinks created by cx_Freeze
    echo "Checking for broken SSL library symlinks..."
    if [ -L "$BUILD_DIR/ncpa/libcrypto.so" ]; then
        crypto_target=$(readlink "$BUILD_DIR/ncpa/libcrypto.so" 2>/dev/null || echo "")
        if [ ! -e "$BUILD_DIR/ncpa/libcrypto.so" ]; then
            echo "INFO: Removing broken libcrypto.so symlink (pointed to: $crypto_target)"
            sudo rm -f "$BUILD_DIR/ncpa/libcrypto.so"
        fi
    fi
    if [ -L "$BUILD_DIR/ncpa/libssl.so" ]; then
        ssl_target=$(readlink "$BUILD_DIR/ncpa/libssl.so" 2>/dev/null || echo "")
        if [ ! -e "$BUILD_DIR/ncpa/libssl.so" ]; then
            echo "INFO: Removing broken libssl.so symlink (pointed to: $ssl_target)"
            sudo rm -f "$BUILD_DIR/ncpa/libssl.so"
        fi
    fi

    # Set permissions (original working approach)
    sudo chmod -R g+r $BUILD_DIR/ncpa
    sudo chmod -R a+r $BUILD_DIR/ncpa
    sudo chown -R nagios:nagios $BUILD_DIR/ncpa/var
    sudo chown nagios:nagios $BUILD_DIR/ncpa/etc $BUILD_DIR/ncpa/etc/*.cfg*
    sudo chown nagios:nagios $BUILD_DIR/ncpa/etc/ncpa.cfg.d $BUILD_DIR/ncpa/etc/ncpa.cfg.d/*
    sudo chmod 755 $BUILD_DIR/ncpa/etc $BUILD_DIR/ncpa/etc/ncpa.cfg.d
    sudo chmod -R 755 $BUILD_DIR/ncpa/var
    sudo chmod 755 $BUILD_DIR/ncpa

    # Build tarball (original working approach)
    echo -e "\nBuilding tarball..."
    cd $BUILD_DIR
    
    # Verify ncpa directory exists before creating tarball
    echo "=== Tarball Creation Debug ==="
    echo "Current directory: $(pwd)"
    echo "BUILD_DIR: $BUILD_DIR"
    echo "NCPA_VER: $NCPA_VER"
    echo "ncpa directory exists: $([ -d "ncpa" ] && echo "YES" || echo "NO")"
    if [ -d "ncpa" ]; then
        echo "ncpa directory size: $(du -sh ncpa 2>/dev/null || echo "unknown")"
        echo "ncpa executable exists: $([ -f "ncpa/ncpa" ] && echo "YES" || echo "NO")"
    else
        echo "ERROR: ncpa directory not found for tarball creation!"
        echo "Available directories in BUILD_DIR:"
        ls -la
        exit 1
    fi
    echo "============================="
    
    # Create tarball copy with platform-specific handling
    # First, ensure any existing target directory is removed
    if [ -d "ncpa-$NCPA_VER" ]; then
        echo "Removing existing ncpa-$NCPA_VER directory..."
        sudo rm -rf "ncpa-$NCPA_VER"
    fi
    
    if [ "$UNAME" == "SunOS" ]; then
        echo "Using Solaris-specific copy method for tarball creation..."
        if command -v gcp >/dev/null 2>&1; then
            # Use GNU cp if available - copy the directory itself
            echo "Using GNU cp to copy ncpa directory..."
            sudo gcp -rf ncpa ncpa-$NCPA_VER
        else
            # Use tar method for standard Solaris cp to avoid cp issues
            echo "Using tar-based copy approach for Solaris..."
            sudo mkdir -p ncpa-$NCPA_VER
            # Use tar to copy directory contents preserving structure
            (cd ncpa && sudo tar cf - .) | (cd ncpa-$NCPA_VER && sudo tar xf -)
        fi
    else
        # Use standard copy for other platforms
        sudo cp -rf ncpa ncpa-$NCPA_VER
    fi
    
    # Verify the copy worked
    echo "ncpa-$NCPA_VER directory created: $([ -d "ncpa-$NCPA_VER" ] && echo "YES" || echo "NO")"
    
    # If Solaris copy failed, try alternative methods
    if [ "$UNAME" == "SunOS" ] && [ ! -d "ncpa-$NCPA_VER" ]; then
        echo "=== Solaris Tarball Copy Failed - Trying Alternative Methods ==="
        
        # Clean up any partial attempt
        sudo rm -rf "ncpa-$NCPA_VER" 2>/dev/null || true
        
        if command -v gcp >/dev/null 2>&1; then
            echo "Attempting with GNU cp (gcp)..."
            sudo gcp -rf ncpa ncpa-$NCPA_VER
        fi
        
        # If gcp also failed or is not available, try find-based copy
        if [ ! -d "ncpa-$NCPA_VER" ]; then
            echo "Attempting find-based copy method..."
            sudo mkdir -p ncpa-$NCPA_VER
            # Use find to copy each top-level item individually
            if [ "$UNAME" == "SunOS" ]; then
                # Solaris find doesn't support -maxdepth, use alternative approach
                for item in ncpa/*; do
                    if [ -e "$item" ]; then
                        sudo cp -rf "$item" "ncpa-$NCPA_VER/"
                    fi
                done
            else
                sudo find ncpa -mindepth 1 -maxdepth 1 -exec cp -rf {} ncpa-$NCPA_VER/ \;
            fi
        fi
        
        echo "Final attempt result: $([ -d "ncpa-$NCPA_VER" ] && echo "SUCCESS" || echo "FAILED")"
        
        # If all methods failed, exit with error
        if [ ! -d "ncpa-$NCPA_VER" ]; then
            echo "ERROR: All copy methods failed on Solaris. Cannot create ncpa-$NCPA_VER directory."
            exit 1
        fi
        echo "============================================="
    fi
    
    if [ "$UNAME" == "AIX" ]; then
        echo -e "***** Build tarball for AIX"
        sudo tar cvf ncpa-$NCPA_VER.tar ncpa-$NCPA_VER | sudo tee -a $BUILD_DIR/build.log
        sudo gzip -f ncpa-$NCPA_VER.tar | sudo tee -a $BUILD_DIR/build.log
    elif [ "$UNAME" == "SunOS" ]; then
        echo -e "***** Build tarball for Solaris"
        # Use gtar if available (GNU tar), otherwise use standard tar
        if command -v gtar >/dev/null 2>&1; then
            sudo gtar -czvf ncpa-$NCPA_VER.tar.gz ncpa-$NCPA_VER | sudo tee -a $BUILD_DIR/build.log
        else
            sudo tar -cf ncpa-$NCPA_VER.tar ncpa-$NCPA_VER | sudo tee -a $BUILD_DIR/build.log
            sudo gzip -f ncpa-$NCPA_VER.tar | sudo tee -a $BUILD_DIR/build.log
        fi
    elif [ "$UNAME" == "Linux" ]; then
        echo -e "***** Build tarball for Linux"
        sudo tar -czvf ncpa-$NCPA_VER.tar.gz ncpa-$NCPA_VER | sudo tee -a $BUILD_DIR/build.log
    fi
)


# --------------------------
# Package
# --------------------------


if [ $BUILD_ONLY -eq 0 ]; then

    # Build package based on system
    echo -e "\nPackaging for system type..."
    
    # Ensure we're in the build directory and verify ncpa directory exists
    cd $BUILD_DIR
    if [ ! -d "ncpa" ]; then
        echo "ERROR: ncpa directory not found for packaging!"
        echo "Current directory: $(pwd)"
        echo "Available directories:"
        ls -la
        echo "Looking for ncpa-* directories..."
        ls -la ncpa-* 2>/dev/null || echo "No ncpa-* directories found"
        exit 1
    fi
    
    echo "✓ Found ncpa directory for packaging"

    if [ "$UNAME" == "Linux" ]; then
        linux/package.sh
    elif [ "$UNAME" == "SunOS" ] || [ "$UNAME" == "Solaris" ]; then
        solaris/package.sh
    elif [ "$UNAME" == "AIX" ]; then
        aix/package.sh
    elif [ "$UNAME" == "Darwin" ]; then
        macos/package.sh
    else
        echo "No packaging method exists. You can locate binaries here:"
        echo "$BUILD_DIR/ncpa"
    fi

    # Remove the build directory and tar.gz
    echo -e "\nClean up packaging dirs..."
    cd $BUILD_DIR
    sudo rm -rf *.tar.gz
    # sudo rm -rf ncpa-$NCPA_VER

fi
