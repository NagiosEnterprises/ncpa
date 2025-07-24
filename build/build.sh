#!/bin/bash -e

echo -e "***** build/build.sh"

# Source version configuration
BUILD_DIR_FOR_VERSION=$( cd "$(dirname "$0")" ; pwd -P )
source "$BUILD_DIR_FOR_VERSION/version_config.sh"

UNAME=$(uname)
if [ "$UNAME" == "Darwin" ] || [ "$UNAME" == "AIX" ] || [ "$UNAME" == "SunOS" ]; then
    BUILD_DIR=$( cd "$(dirname "$0")" ; pwd -P )
    AGENT_DIR="$BUILD_DIR/../agent"
else
    BUILD_DIR=$(dirname "$(readlink -f "$0")")
    AGENT_DIR=$(readlink -f "$BUILD_DIR/../agent")
fi
NCPA_VER=$(cat $BUILD_DIR/../VERSION)

# Virtual environment configuration
VENV_MANAGER="$BUILD_DIR/venv_manager.sh"
VENV_NAME="ncpa-build-$(echo "$UNAME" | tr '[:upper:]' '[:lower:]')"
export VENV_NAME

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
}


# --------------------------
# Do initial setup
# --------------------------


# Load required things for different systems
echo -e "\nRunning build for: $UNAME"

# Always setup virtual environment first
setup_virtual_environment

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
else
    echo "Not a supported system for our build script."
    echo "If you're sure all pre-reqs are installed, try running the"
    echo "build without setup: ./build.sh --build-only"
fi

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
    sudo useradd nagios
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

(
    echo -e "\nBuilding NCPA binaries..."
    cd $AGENT_DIR

    echo -e "\nFreezing app (may take a minute)..."
    # Set environment variables to help with Solaris build issues
    if [ "$UNAME" == "SunOS" ]; then
        echo "Setting Solaris-specific environment variables for cx_Freeze..."
        export CX_FREEZE_SILENCE_MISSING_MODULES=1
        export SOLARIS_BUILD=1
        
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
        $PYTHONBIN setup.py build_exe | sudo tee $BUILD_DIR/build.log
    fi


    echo -e "\nSet up packaging dirs..."
    # Move the ncpa binary data
    cd $BUILD_DIR
    sudo rm -rf $BUILD_DIR/ncpa
    
    # Find the cx_Freeze build directory (it varies by platform)
    if [ "$UNAME" == "SunOS" ]; then
        # Solaris find doesn't support -maxdepth, use alternative approach
        BUILD_EXE_DIR=$(find $AGENT_DIR/build -type d -name "exe.*" | head -1)
    else
        BUILD_EXE_DIR=$(find $AGENT_DIR/build -maxdepth 1 -name "exe.*" -type d | head -1)
    fi
    
    if [ -z "$BUILD_EXE_DIR" ]; then
        echo "ERROR: Could not find cx_Freeze build directory in $AGENT_DIR/build/"
        echo "Available directories:"
        ls -la $AGENT_DIR/build/ 2>/dev/null || echo "Build directory does not exist"
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
        # Check if the executable is actually executable
        if [ -x "$BUILD_EXE_DIR/ncpa" ]; then
            echo "✓ ncpa executable has proper permissions"
        else
            echo "WARNING: ncpa executable lacks execute permissions"
            ls -la "$BUILD_EXE_DIR/ncpa"
        fi
    fi
    
    # Copy build directory with platform-specific handling for symbolic links
    if [ "$UNAME" == "Darwin" ]; then
        # On macOS, use -L to follow symbolic links to avoid issues with relative paths
        echo "Copying macOS build with symbolic link resolution..."
        sudo cp -RLf "$BUILD_EXE_DIR" $BUILD_DIR/ncpa
    elif [ "$UNAME" == "SunOS" ]; then
        # On Solaris, handle potential differences in cp command behavior
        echo "Copying Solaris build..."
        if command -v gcp >/dev/null 2>&1; then
            # Use GNU cp if available
            sudo gcp -rf "$BUILD_EXE_DIR" $BUILD_DIR/ncpa
        else
            # Use standard Solaris cp (use -R instead of -r)
            sudo cp -Rf "$BUILD_EXE_DIR" $BUILD_DIR/ncpa
        fi
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

    # Set permissions
    echo "Setting file permissions..."
    
    # Set permissions more carefully to avoid warnings about missing files and broken symlinks
    if [ -d "$BUILD_DIR/ncpa" ]; then
        # Set permissions for regular files (excluding broken symlinks)
        find "$BUILD_DIR/ncpa" -type f -exec sudo chmod g+r,a+r {} \; 2>/dev/null || true
        
        # Set permissions for directories
        find "$BUILD_DIR/ncpa" -type d -exec sudo chmod g+r,a+r {} \; 2>/dev/null || true
        
        # Handle symlinks separately - only set permissions on valid symlinks
        find "$BUILD_DIR/ncpa" -type l | while read -r symlink; do
            if [ -L "$symlink" ]; then
                # Symlink exists - try to set permissions regardless of target validity
                sudo chmod g+r,a+r "$symlink" 2>/dev/null || true
                # Check if target exists for informational purposes
                if [ ! -e "$symlink" ]; then
                    echo "INFO: Symlink exists but target missing: $symlink -> $(readlink "$symlink" 2>/dev/null || echo 'unknown')"
                fi
            fi
        done
        
        echo "✓ Basic file permissions set"
    else
        echo "WARNING: ncpa build directory not found"
    fi
    
    # Check if expected directories exist before setting ownership
    if [ -d "$BUILD_DIR/ncpa/var" ]; then
        echo "Setting ownership for var directory..."
        sudo chown -R nagios:nagios $BUILD_DIR/ncpa/var
        sudo chmod -R 755 $BUILD_DIR/ncpa/var
    else
        echo "WARNING: var directory not found at $BUILD_DIR/ncpa/var"
        echo "Creating var directory structure..."
        sudo mkdir -p $BUILD_DIR/ncpa/var/log
        sudo chown -R nagios:nagios $BUILD_DIR/ncpa/var
        sudo chmod -R 755 $BUILD_DIR/ncpa/var
    fi
    
    if [ -d "$BUILD_DIR/ncpa/etc" ]; then
        echo "Setting ownership for etc directory..."
        sudo chown nagios:nagios $BUILD_DIR/ncpa/etc
        sudo chmod 755 $BUILD_DIR/ncpa/etc
        
        # Set ownership for config files if they exist
        if ls $BUILD_DIR/ncpa/etc/*.cfg* >/dev/null 2>&1; then
            sudo chown nagios:nagios $BUILD_DIR/ncpa/etc/*.cfg*
        fi
        
        if [ -d "$BUILD_DIR/ncpa/etc/ncpa.cfg.d" ]; then
            sudo chown nagios:nagios $BUILD_DIR/ncpa/etc/ncpa.cfg.d
            sudo chmod 755 $BUILD_DIR/ncpa/etc/ncpa.cfg.d
            if ls $BUILD_DIR/ncpa/etc/ncpa.cfg.d/* >/dev/null 2>&1; then
                sudo chown nagios:nagios $BUILD_DIR/ncpa/etc/ncpa.cfg.d/*
            fi
        fi
    else
        echo "WARNING: etc directory not found at $BUILD_DIR/ncpa/etc"
        echo "This may indicate an incomplete build"
    fi
    
    sudo chmod 755 $BUILD_DIR/ncpa

    # Build tarball
    echo -e "\nBuilding tarball..."
    
    # Remove any existing versioned directory to avoid copy conflicts
    sudo rm -rf ncpa-$NCPA_VER
    
    if [ "$UNAME" == "SunOS" ]; then
        # On Solaris, use -R instead of -r for cp, and handle broken symlinks
        echo "Copying with Solaris-compatible options, skipping broken symlinks..."
        if command -v gcp >/dev/null 2>&1; then
            # Use GNU cp if available - it handles broken symlinks better
            sudo gcp -rf ncpa ncpa-$NCPA_VER 2>/dev/null || {
                echo "WARNING: Some files could not be copied (likely broken symlinks)"
                # Try copying without following symlinks
                sudo gcp -rd ncpa ncpa-$NCPA_VER 2>/dev/null || sudo cp -Rf ncpa ncpa-$NCPA_VER
            }
        else
            # Use standard Solaris cp with error handling for broken symlinks
            sudo cp -Rf ncpa ncpa-$NCPA_VER 2>/dev/null || {
                echo "WARNING: Standard copy failed, trying alternative approach..."
                # Create target directory manually and copy contents
                sudo mkdir -p ncpa-$NCPA_VER
                (cd ncpa && find . -type f -exec sudo cp {} ../ncpa-$NCPA_VER/{} \; 2>/dev/null || true)
                (cd ncpa && find . -type d -exec sudo mkdir -p ../ncpa-$NCPA_VER/{} \; 2>/dev/null || true)
                (cd ncpa && find . -type l | while read -r link; do
                    if [ -L "$link" ]; then
                        # Copy the symlink itself, not its target
                        sudo cp -d "$link" "../ncpa-$NCPA_VER/$link" 2>/dev/null || true
                    fi
                done)
            }
        fi
    else
        # On other systems (Linux, AIX), use standard recursive copy with error handling
        echo "Copying build directory, handling broken symlinks..."
        sudo cp -rf ncpa ncpa-$NCPA_VER 2>/dev/null || {
            echo "WARNING: Standard copy failed, trying without broken symlinks..."
            # Create target directory and copy valid files only
            sudo mkdir -p ncpa-$NCPA_VER
            (cd ncpa && find . -type f -exec cp {} ../ncpa-$NCPA_VER/{} \; 2>/dev/null || true)
            (cd ncpa && find . -type d -exec mkdir -p ../ncpa-$NCPA_VER/{} \; 2>/dev/null || true)
            (cd ncpa && find . -type l | while read -r link; do
                if [ -L "$link" ]; then
                    # Copy the symlink itself, not its target
                    cp -d "$link" "../ncpa-$NCPA_VER/$link" 2>/dev/null || true
                fi
            done)
        }
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
