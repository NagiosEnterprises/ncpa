#!/bin/bash -e

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
    . $BUILD_DIR/osx/setup.sh
else
    echo "Not a supported system for our build script."
    echo "If you're sure all pre-reqs are installed, try running the"
    echo "build without setup: ./build.sh --build-only"
fi


# Move the ncpa binary data
cd $BUILD_DIR
rm -rf $BUILD_DIR/ncpa
cp -rf $AGENT_DIR/build/exe.* $BUILD_DIR/ncpa

# REMOVE LIBFFI COPY - PLEASE CHANGE THIS LATER
# It should be in .libs_cffi_backend for proper linking and
# possibly in the future we will fix this but we have to include
# the exact version ... this will delete the duplicate which should
# have a special name like libffi-6322464e.so.6.0.4
rm -f $BUILD_DIR/ncpa/libffi-*.so.*

# Set permissions
chmod -R g+r $BUILD_DIR/ncpa
chmod -R a+r $BUILD_DIR/ncpa
chown nagios:nagios $BUILD_DIR/ncpa/var
chown nagios:nagios $BUILD_DIR/ncpa/etc $BUILD_DIR/ncpa/etc/*.cfg*
chown nagios:nagios $BUILD_DIR/ncpa/etc/ncpa.cfg.d $BUILD_DIR/ncpa/etc/ncpa.cfg.d/*
chmod 755 $BUILD_DIR/ncpa/etc $BUILD_DIR/ncpa/etc/ncpa.cfg.d
chmod 755 $BUILD_DIR/ncpa/var
chmod 755 $BUILD_DIR/ncpa

# Build tarball
echo -e "***** Build tarball"
cp -rf ncpa ncpa-$NCPA_VER
if [ "$UNAME" == "AIX" ]; then
    tar cvf ncpa-$NCPA_VER.tar ncpa-$NCPA_VER >> $BUILD_DIR/build.log
    gzip -f ncpa-$NCPA_VER.tar >> $BUILD_DIR/build.log
elif [ "$UNAME" == "Linux" ]; then
    tar -czvf ncpa-$NCPA_VER.tar.gz ncpa-$NCPA_VER >> $BUILD_DIR/build.log
fi
echo -e "***** ls -al"
ls -al
echo -e "***** Tail build.log"
tail $BUILD_DIR/build.log

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
    osx/package.sh
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

