#!/bin/bash -e

# Set global build opts
DIR=$(dirname "$(readlink -f "$0")")
BUILD_DIR=$(realpath "$DIR/..")
BUILD_RPM_DIR="/tmp/test/usr/src/redhat"
VERSION=$(cat $BUILD_DIR/../VERSION)

# Build spec file
cd $BUILD_DIR
cat linux/ncpa.spec | sed "s/__VERSION__/$VERSION/g" | sed "s|__BUILDROOT__|$BUILD_RPM_DIR|g" > $BUILD_DIR/ncpa.spec

# Build rpm package (also used on Debian systems)
(
    mkdir -p $BUILD_RPM_DIR/SPECS
    mkdir -p $BUILD_RPM_DIR/SRPMS
    mkdir -p $BUILD_RPM_DIR/RPMS
    mkdir -p $BUILD_RPM_DIR/SOURCES
    mkdir -p $BUILD_RPM_DIR/BUILD
    cp -f $BUILD_DIR/ncpa-$VERSION.tar.gz $BUILD_RPM_DIR/SOURCES/
    rm -f $BUILD_RPM_DIR/SPECS/ncpa.spec
    cp -f $BUILD_DIR/ncpa.spec $BUILD_RPM_DIR/SPECS/
    QA_RPATHS='$[ 0x0002 ]' rpmbuild $BUILD_RPM_DIR/SPECS/ncpa.spec -bb --define "_topdir $BUILD_RPM_DIR"
    find $BUILD_RPM_DIR/RPMS -name "ncpa-$VERSION*" -exec cp {} . \;
)
