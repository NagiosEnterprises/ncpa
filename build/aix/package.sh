#!/bin/bash -e

# Set global build opts
DIR=$( cd "$(dirname "$0")" ; pwd -P )
BUILD_DIR="$DIR/.."
NCPA_VER=$(cat $BUILD_DIR/../VERSION)
BUILD_RPM_DIR="/tmp/test/usr/src/redhat"
REQUIRED_LIBS="libpython3.12.a libgcc_s.a libintl.a libiconv.a libsqlite3.a libssl.a libcrypto.a libz.a libffi.a"

# Build spec file
cd $BUILD_DIR

# Verify standalone runtime libraries are present before packaging
echo -e "***** aix/package.sh - verifying bundled AIX runtime libraries"
missing=0
for lib in $REQUIRED_LIBS; do
    if [ -f "$BUILD_DIR/ncpa/lib/$lib" ]; then
        echo "  Found ncpa/lib/$lib"
    else
        echo "  Missing ncpa/lib/$lib"
        missing=1
    fi
done
if [ "$missing" -ne 0 ]; then
    echo "ERROR: Cannot package AIX NCPA without bundled runtime libraries."
    echo "Expected under ncpa/lib: $REQUIRED_LIBS"
    exit 1
fi

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
