#!/bin/bash -e

echo -e "***** build/build.sh"

# Global variables
PYTHONVER="3.13.5"
SSLVER="3.0.17"
ZLIBVER="1.3.1"

UNAME=$(uname)
if [ "$UNAME" == "Darwin" ] || [ "$UNAME" == "AIX" ] || [ "$UNAME" == "SunOS" ]; then
    BUILD_DIR=$( cd "$(dirname "$0")" ; pwd -P )
    AGENT_DIR="$BUILD_DIR/../agent"
else
    BUILD_DIR=$(dirname "$(readlink -f "$0")")
    AGENT_DIR=$(readlink -f "$BUILD_DIR/../agent")
fi
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
    sudo rm -rf $BUILD_DIR/ncpa-*
    sudo rm -rf $AGENT_DIR/build
    sudo rm -rf $BUILD_DIR/NCPA-INSTALL-*
    sudo rm -f $BUILD_DIR/*.rpm $BUILD_DIR/*.dmg $BUILD_DIR/*.deb
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
    esac
    shift
done


# --------------------------
# Do initial setup
# --------------------------


# Load required things for different systems
echo -e "\nRunning build for: $UNAME"
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
    if { [ ! -f $BUILD_DIR/prereqs.installed ] && [ $SKIP_SETUP -eq 0 ]; } || ! which $PYTHONBIN > /dev/null; then
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
    python -m pip install -r resources/require.txt --upgrade
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
    sudo cp -rf $AGENT_DIR/build/exe.* $BUILD_DIR/ncpa
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
    if [ "$UNAME" == "AIX" ]; then
        echo -e "***** Build tarball"
        sudo tar cvf ncpa-$NCPA_VER.tar ncpa-$NCPA_VER | sudo tee -a $BUILD_DIR/build.log
        sudo gzip -f ncpa-$NCPA_VER.tar | sudo tee -a $BUILD_DIR/build.log
    elif [ "$UNAME" == "Linux" ]; then
        echo -e "***** Build tarball"
        sudo tar -czvf ncpa-$NCPA_VER.tar.gz ncpa-$NCPA_VER | sudo tee -a $BUILD_DIR/build.log
    fi
)


# --------------------------
# Package
# --------------------------


if [ $BUILD_ONLY -eq 0 ]; then

    # Build package based on system
    echo -e "\nPackaging for system type..."

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
    sudo rm -rf ncpa-$NCPA_VER

fi
