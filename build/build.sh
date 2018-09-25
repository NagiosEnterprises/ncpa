#!/bin/bash -e

# Global variables
UNAME=$(uname)
BUILD_DIR=$(dirname "$(readlink -f "$0")")
AGENT_DIR=$(realpath "$DIR/../agent")

# Get the arguments passed to us


# Load required things for different systems
if [ "$UNAME" == "Linux" ]; then
    . linux/setup.sh
elif [ "$UNAME" == "SunOS" ] || [ "$UNAME" == "Solaris" ]; then
    . solaris/setup.sh
elif [ "$UNAME" == "Darwin" ]; then
    . osx/setup.sh
else 
    echo "Not a supported system for our build script. Try running build manually with:"
    echo " sh build.sh --manual"
fi

# Check that pre-reqs have been installed
if [ ! -f prereqs.installed ]; then
    install_prereqs
else
    echo "Could not automatically determine system type."
    echo "Please run the setup.sh script in the folder for the build type below:"
    echo " - linux"
    echo " - osx"
    echo " - aix"
    echo " - solaris"
fi

# Update the required python modules


# Build the python with cx_Freeze

find $AGENT_DIR -name *.pyc -exec rm '{}' \;
mkdir -p $AGENT_DIR/plugins
mkdir -p $AGENT_DIR/build
mkdir -p $AGENT_DIR/var/log
cat /dev/null > $AGENT_DIR/var/log/ncpa_passive.log
cat /dev/null > $AGENT_DIR/var/log/ncpa_listener.log

(
    cd $AGENT_DIR && $PYTHONBIN setup_posix.py build_exe
    cp -rf $(BASEDIR)/agent/build/exe.* $BUILD_DIR/ncpa
)



