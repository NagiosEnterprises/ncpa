#!/bin/bash -e

# Set global build opts
DIR=$(dirname "$(readlink -f "$0")")
BUILD_DIR=$(readlink -f "$DIR/..")
BUILD_RPM_DIR="/tmp/test/usr/src/redhat"
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
    cp ncpa-$NCPA_VER.tar.gz $BUILD_RPM_DIR/SOURCES/
    rm -f $BUILD_RPM_DIR/SPECS/ncpa.spec
    cp -f ncpa.spec $BUILD_RPM_DIR/SPECS/
    rpmbuild -bb --define "_topdir $BUILD_RPM_DIR" $BUILD_RPM_DIR/SPECS/ncpa.spec
    find $BUILD_RPM_DIR/RPMS -name "ncpa-$NCPA_VER*" -exec cp {} . \;
)
