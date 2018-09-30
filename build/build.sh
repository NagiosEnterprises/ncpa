#!/bin/bash -e

# Global variables
UNAME=$(uname)
BUILD_DIR=$(dirname "$(readlink -f "$0")")
AGENT_DIR=$(realpath "$BUILD_DIR/../agent")
MANUAL=0

# Get the arguments passed to us


# Load required things for different systems
echo "Running build for: $UNAME"
if [ "$UNAME" == "Linux" ]; then
    . linux/setup.sh
elif [ "$UNAME" == "SunOS" ] || [ "$UNAME" == "Solaris" ]; then
    . solaris/setup.sh
elif [ "$UNAME" == "Darwin" ]; then
    . osx/setup.sh
else 
    echo "Not a supported system for our build script."
    echo "If you're sure all pre-reqs are installed, try running the"
    echo "build manually: sh build.sh --manual"
fi

# Check that pre-reqs have been installed
if [ ! -f prereqs.installed ] || [ $MANUAL -eq 1 ]; then
    read -r -p "Automatically install system pre-reqs? [Y/n]" resp
    if [[ $resp =~ ^(yes|y|Y| ) ]] || [[ -z $resp ]]; then
        install_prereqs
        touch prereqs.installed
    fi
fi

# Update the required python modules



# Build the python with cx_Freeze
echo "Building NCPA binaries..."

find $AGENT_DIR -name *.pyc -exec rm '{}' \;
mkdir -p $AGENT_DIR/plugins
mkdir -p $AGENT_DIR/build
mkdir -p $AGENT_DIR/var/log
cat /dev/null > $AGENT_DIR/var/log/ncpa_passive.log
cat /dev/null > $AGENT_DIR/var/log/ncpa_listener.log

(
    cd $AGENT_DIR
    $PYTHONBIN setup_posix.py build_exe > $BUILD_DIR/build.log
    rm -rf $BUILD_DIR/ncpa
    cp -rf $AGENT_DIR/build/exe.* $BUILD_DIR/ncpa
    chown root:nagios $BUILD_DIR/ncpa/var
    chmod 775 $BUILD_DIR/ncpa/var
)

# Build package based on system
echo "Packaging for system type..."

if [ "$UNAME" == "Linux" ]; then
    . linux/package.sh
elif [ "$UNAME" == "SunOS" ] || [ "$UNAME" == "Solaris" ]; then
    . solaris/package.sh
elif [ "$UNAME" == "Darwin" ]; then
    . osx/package.sh
else
    echo "No packaging method exists. You can locate binaries here:"
    echo "$BUILD_DIR/ncpa"
fi

