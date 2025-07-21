#!/bin/bash -e

# Set global build opts
DIR=$( cd "$(dirname "$0")" ; pwd -P )
BUILD_DIR="$DIR/.."
NCPA_VER=$(cat $BUILD_DIR/../VERSION)
BUILD_RPM_DIR="/tmp/test/usr/src/redhat"

# Build spec file
cd $BUILD_DIR

# Determine release number by checking for existing RPMs
RELEASE=1
while true; do
    # Check if RPM with this release already exists
    if ls $BUILD_DIR/ncpa-$NCPA_VER-$RELEASE.*.rpm 2>/dev/null >&2; then
        echo -e "***** Found existing RPM with release $RELEASE, incrementing..."
        RELEASE=$((RELEASE + 1))
    else
        echo -e "***** Using release number: $RELEASE"
        break
    fi
done

cat aix/ncpa.spec | sed "s/__VERSION__/$NCPA_VER/g" | sed "s|__BUILDROOT__|$BUILD_RPM_DIR|g" | sed "s/^Release:[[:space:]]*1/Release:\t$RELEASE/" > $BUILD_DIR/ncpa.spec

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
