#!/bin/bash -e

echo -e "***** build/build.sh"

# Source version configuration
BUILD_DIR_FOR_VERSION=$( cd "$(dirname "$0")" ; pwd -P )
source "$BUILD_DIR_FOR_VERSION/version_config.sh"

UNAME=$(uname)
BUILD_DIR=$( cd "$(dirname "$0")" ; pwd -P )
AGENT_DIR="$BUILD_DIR/../agent"
NCPA_VER=$(cat $BUILD_DIR/../VERSION)

# User-defined variables
SKIP_SETUP=0
PACKAGE_ONLY=0
BUILD_ONLY=0
BUILD_TRAVIS=0
NO_INTERACTION=0


# --------------------------
# General functions
# --------------------------


usage() {
    echo "Use the build.sh script to setup build environment, compile, and package builds for MacOS/Darwin."
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
    echo "  -c | --clean        Clean up the build directory"
    echo "  -n | --no-interaction  Run without interactive prompts (auto-confirm)"
    echo ""
    echo "Operating System Supported: MacOS/Darwin only."
    echo ""
}


clean_build_dir() {
    echo -e "\n***** build/build.sh - Cleaning up build directory..."
    for dir in "$BUILD_DIR"/ncpa-*; do
        if [ -d "$dir" ]; then
            sudo rm -rf "$dir"
        fi
    done
    sudo rm -rf $AGENT_DIR/build
    sudo rm -rf $BUILD_DIR/NCPA-INSTALL-*
    sudo rm -f $BUILD_DIR/ncpa.spec
    sudo rm -f $BUILD_DIR/*.tar.gz
    sudo rm -rf $BUILD_ROOT
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
    esac
    shift
done


# --------------------------
# Do initial setup
# --------------------------


echo -e "\nRunning build for: $UNAME"
if [ "$UNAME" == "Darwin" ]; then
    . $BUILD_DIR/macos/setup.sh
else
    echo "Not a supported system for our build script."
    exit 1
fi

if [ $PACKAGE_ONLY -eq 0 ] && [ $BUILD_ONLY -eq 0 ]; then
    if { [ ! -f $BUILD_DIR/prereqs.installed ] && [ $SKIP_SETUP -eq 0 ]; } || ! which $PYTHONBIN > /dev/null; then
        echo "** WARNING: This should not be done on a production system. **"
        if [ $NO_INTERACTION -eq 1 ] || { read -r -p "Automatically install system pre-reqs? [Y/n] " resp && [[ $resp =~ ^(yes|y|Y| ) ]] || [[ -z $resp ]]; }; then
            install_prereqs
            sudo touch $BUILD_DIR/prereqs.installed
        fi
    fi
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

if command -v git > /dev/null; then
    GIT_LONG=$(git rev-parse HEAD)
    GIT_SHORT=$(git rev-parse --short HEAD)
    GIT_UNCOMMITTED=$(git status --untracked-files=no --porcelain)
    # echo "GIT_UNCOMMITTED: $GIT_UNCOMMITTED"
    if [ "$GIT_UNCOMMITTED" ]; then
        GIT_LONG="$GIT_LONG++  compiled with uncommitted changes"
        GIT_SHORT="$GIT_SHORT++"
    fi
    GIT_HASH_FILE="git-$GIT_SHORT.githash"
    # echo "GIT_LONG: $GIT_LONG"
    # echo "GIT_SHORT: $GIT_SHORT"
    echo "GIT_HASH_FILE: $GIT_HASH_FILE"
fi

(
    echo -e "\nBuilding NCPA binaries..."
    cd $AGENT_DIR

    echo -e "\nFreezing app (may take a minute)..."
    $PYTHONBIN setup.py build_exe | sudo tee $BUILD_DIR/build.log


    echo -e "\nSet up packaging dirs..."
    # Move the ncpa binary data
    cd $BUILD_DIR
    sudo rm -rf $BUILD_DIR/ncpa
    
    # Find the cx_Freeze build directory (it varies by platform)
    BUILD_EXE_DIR=$(find $AGENT_DIR/build -maxdepth 1 -name "exe.*" -type d | head -1)
    
    if [ -z "$BUILD_EXE_DIR" ]; then
        echo "ERROR: Could not find cx_Freeze build directory in $AGENT_DIR/build/"
        echo "Available directories:"
        ls -la $AGENT_DIR/build/
        exit 1
    fi
    
    echo "Found cx_Freeze build directory: $BUILD_EXE_DIR"
    echo "UNAME: $UNAME"
    
    # Copy build directory with platform-specific handling for symbolic links
    # On macOS, use -L to follow symbolic links to avoid issues with relative paths
    sudo cp -RLf "$BUILD_EXE_DIR" $BUILD_DIR/ncpa
    
    echo $GIT_LONG | sudo tee $BUILD_DIR/ncpa/$GIT_HASH_FILE

    # REMOVE LIBFFI COPY - PLEASE CHANGE THIS LATER
    # It should be in .libs_cffi_backend for proper linking and
    # possibly in the future we will fix this but we have to include
    # the exact version ... this will delete the duplicate which should
    # have a special name like libffi-6322464e.so.6.0.4
    sudo rm -f $BUILD_DIR/ncpa/libffi-*.so.*

    # Set permissions
    sudo chmod -R g+r $BUILD_DIR/ncpa
    sudo chmod -R a+r $BUILD_DIR/ncpa
    sudo chown -R nagios:nagios $BUILD_DIR/ncpa/var
    sudo chown nagios:nagios $BUILD_DIR/ncpa/etc $BUILD_DIR/ncpa/etc/*.cfg*
    sudo chown nagios:nagios $BUILD_DIR/ncpa/etc/ncpa.cfg.d $BUILD_DIR/ncpa/etc/ncpa.cfg.d/*
    sudo chmod 755 $BUILD_DIR/ncpa/etc $BUILD_DIR/ncpa/etc/ncpa.cfg.d
    sudo chmod -R 755 $BUILD_DIR/ncpa/var
    sudo chmod 755 $BUILD_DIR/ncpa

    # Build tarball
    echo -e "\nBuilding tarball..."
    sudo cp -rf ncpa ncpa-$NCPA_VER
    echo -e "***** Build tarball"
    sudo tar -czvf ncpa-$NCPA_VER.tar.gz ncpa-$NCPA_VER | sudo tee -a $BUILD_DIR/build.log
)


# --------------------------
# Package
# --------------------------


if [ $BUILD_ONLY -eq 0 ]; then
    echo -e "\nPackaging for MacOS..."
    macos/package.sh
    echo -e "\nClean up packaging dirs..."
    cd $BUILD_DIR
    sudo rm -rf *.tar.gz
fi
