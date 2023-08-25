#!/bin/bash -e

echo -e "***** build/build_github.sh"

# Global variables
UNAME=$(uname)
if [ "$UNAME" == "Darwin" ] || [ "$UNAME" == "AIX" ] || [ "$UNAME" == "SunOS" ]; then
    BUILD_DIR=$( cd "$(dirname "$0")" ; pwd -P )
    AGENT_DIR="$BUILD_DIR/../agent"
else
    BUILD_DIR=$(dirname "$(readlink -f "$0")")
    AGENT_DIR=$(readlink -f "$BUILD_DIR/../agent")
fi
NCPA_VER=$(cat $BUILD_DIR/../VERSION)

echo "***** UNAME: $UNAME, BUILD_DIR: $BUILD_DIR, AGENT_DIR: $AGENT_DIR"

echo -e "***** Initial setup"
if [ "$UNAME" == "Linux" ]; then
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

# Add file with current GIT hash to build
GIT_LONG="Not built under GIT"
GIT_HASH_FILE="NoGIT.githash"

if command -v git > /dev/null; then
    GIT_LONG=$(git rev-parse HEAD)
    GIT_SHORT=$(git rev-parse --short HEAD)
    GIT_UNCOMMITTED=$(git status --untracked-files=no --porcelain)
    echo "GIT_UNCOMMITTED: $GIT_UNCOMMITTED"
    if [ "$GIT_UNCOMMITTED" ]; then
        GIT_LONG="$GIT_LONG++  compiled with uncommitted changes"
        GIT_SHORT="$GIT_SHORT++"
    fi
    GIT_HASH_FILE="git-$GIT_SHORT.githash"
    echo "GIT_LONG: $GIT_LONG"
    echo "GIT_SHORT: $GIT_SHORT"
    echo "GIT_HASH_FILE: $GIT_HASH_FILE"
fi

# Move the ncpa binary data
cd $BUILD_DIR
rm -rf $BUILD_DIR/ncpa
cp -rf $AGENT_DIR/build/exe.* $BUILD_DIR/ncpa
echo $GIT_LONG >  $BUILD_DIR/ncpa/$GIT_HASH_FILE

# REMOVE LIBFFI COPY - PLEASE CHANGE THIS LATER
# It should be in .libs_cffi_backend for proper linking and
# possibly in the future we will fix this but we have to include
# the exact version ... this will delete the duplicate which should
# have a special name like libffi-6322464e.so.6.0.4
rm -f $BUILD_DIR/ncpa/libffi-*.so.*

# Set permissions
sudo chmod -R g+r $BUILD_DIR/ncpa
sudo chmod -R a+r $BUILD_DIR/ncpa
sudo chown nagios:nagios $BUILD_DIR/ncpa/var
sudo chown nagios:nagios $BUILD_DIR/ncpa/etc $BUILD_DIR/ncpa/etc/*.cfg*
sudo chown nagios:nagios $BUILD_DIR/ncpa/etc/ncpa.cfg.d $BUILD_DIR/ncpa/etc/ncpa.cfg.d/*
sudo chmod 755 $BUILD_DIR/ncpa/etc $BUILD_DIR/ncpa/etc/ncpa.cfg.d
sudo chmod 755 $BUILD_DIR/ncpa/var
sudo chmod 755 $BUILD_DIR/ncpa

# Build tarball for AIX and Linux
cp -rf ncpa ncpa-$NCPA_VER
if [ "$UNAME" == "AIX" ]; then
    echo -e "***** Build tarball"
    tar cvf ncpa-$NCPA_VER.tar ncpa-$NCPA_VER >> $BUILD_DIR/build.log
    gzip -f ncpa-$NCPA_VER.tar >> $BUILD_DIR/build.log
elif [ "$UNAME" == "Linux" ]; then
    echo -e "***** Build tarball"
    tar -czvf ncpa-$NCPA_VER.tar.gz ncpa-$NCPA_VER >> $BUILD_DIR/build.log
fi
echo -e "***** ls -al"
ls -al
echo -e "***** ls -al ncpa"
ls -al ncpa
echo -e "***** ls -al ncpa-$NCPA_VER"
ls -al ncpa-$NCPA_VER
echo -e "***** ls -al ncpa-$NCPA_VER/listener"
ls -al ncpa-$NCPA_VER/listener

# echo -e "***** Tail build.log"
# tail $BUILD_DIR/build.log

# --------------------------
# Package
# --------------------------



# Build package based on system
echo "***** Packaging for system type..."

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
echo -e "***** ls -al"
ls -al

# Remove the build directory and tar.gz
# cd $BUILD_DIR
# rm -rf *.tar.gz
# rm -rf ncpa-$NCPA_VER

