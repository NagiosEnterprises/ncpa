#!/bin/bash

echo -e "***** macos/package.sh"

# Get version
DIR=$( cd "$(dirname "$0")" ; pwd -P )
BUILD_DIR="$DIR/.."
NCPA_VER=$(cat $BUILD_DIR/../VERSION)
ARCH=$(arch)

(
    # Move .dylib files into lib folder. TODO: should this be done somewhere else?
    mv ncpa-$NCPA_VER/*.dylib ncpa-$NCPA_VER/lib

    mkdir NCPA-INSTALL-$NCPA_VER
    mv ncpa-$NCPA_VER NCPA-INSTALL-$NCPA_VER/ncpa
    cp NCPA-INSTALL-$NCPA_VER/ncpa/build_resources/macosuninstall.sh NCPA-INSTALL-$NCPA_VER/ncpa/uninstall.sh
    cp NCPA-INSTALL-$NCPA_VER/ncpa/build_resources/macosreadme.txt NCPA-INSTALL-$NCPA_VER/readme.txt
    mv NCPA-INSTALL-$NCPA_VER/ncpa/build_resources/macosinstall.sh NCPA-INSTALL-$NCPA_VER/install.sh

    # Create MacOS disk image file
    hdiutil create -volname NCPA-$NCPA_VER -srcfolder NCPA-INSTALL-$NCPA_VER -ov -format UDZO ncpa_$NCPA_VER-1_amd64.dmg
)
