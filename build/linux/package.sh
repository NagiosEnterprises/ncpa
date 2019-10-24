#!/bin/bash -e

# Set global build opts
DIR=$(dirname "$(readlink -f "$0")")
BUILD_DIR=$(readlink -f "$DIR/..")
BUILD_RPM_DIR="/usr/src/redhat"

# Get information about system
. $BUILD_DIR/linux/init.sh
NCPA_VER=$(cat $BUILD_DIR/../VERSION)

# Build spec file
cd $BUILD_DIR
cat linux/ncpa.spec | sed "s/__VERSION__/$NCPA_VER/g" | sed "s|__BUILDROOT__|$BUILD_RPM_DIR|g" > $BUILD_DIR/ncpa.spec

# Build rpm package (also used on Debian systems)
(
    mkdir -p $BUILD_RPM_DIR/SPECS
    mkdir -p $BUILD_RPM_DIR/SRPMS
    mkdir -p $BUILD_RPM_DIR/RPMS
    mkdir -p $BUILD_RPM_DIR/SOURCES
    mkdir -p $BUILD_RPM_DIR/BUILD
    cp -f $BUILD_DIR/ncpa-$NCPA_VER.tar.gz $BUILD_RPM_DIR/SOURCES/
    rm -f $BUILD_RPM_DIR/SPECS/ncpa.spec
    cp -f $BUILD_DIR/ncpa.spec $BUILD_RPM_DIR/SPECS/

    if [ "$distro" == "Raspbian" ]; then
        parch=`uname -m`
        QA_RPATHS='$[ 0x0002 ]' rpmbuild $BUILD_RPM_DIR/SPECS/ncpa.spec -bb --target=armhf --define "_topdir $BUILD_RPM_DIR" --define "_arch armhf" >> $BUILD_DIR/build.log
    else
        QA_RPATHS='$[ 0x0002 ]' rpmbuild $BUILD_RPM_DIR/SPECS/ncpa.spec -bb --define "_topdir $BUILD_RPM_DIR" >> $BUILD_DIR/build.log
    fi

    find $BUILD_RPM_DIR/RPMS -name "ncpa-$NCPA_VER*" -exec cp {} . \;
)

# Convert into a deb package for Debian systems
if [ "$distro" == "Debian" ] || [ "$distro" == "Ubuntu" ] || [ "$distro" == "Raspbian" ]; then

    cd $BUILD_DIR
    mkdir -p debbuild
    cp *.rpm debbuild/
    cd debbuild

    # Create deb package with alien
    rpm="*.rpm "
    if [ "$distro" == "Raspbian" ]; then
        rpm="*armhf.rpm"
    fi

    alien -c -k -v $rpm >> $BUILD_DIR/build.log
    
    cd $BUILD_DIR
    cp debbuild/*.deb .
    
    rm -rf *.rpm
    rm -rf debbuild

fi
