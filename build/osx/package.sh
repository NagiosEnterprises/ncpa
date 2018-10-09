#!/bin/bash

# Get version
DIR=$(dirname "$0")
BUILD_DIR="$DIR/.."
VERSION=$(cat $BUILD_DIR/../VERSION)
ARCH=$(arch)

(
    mkdir NCPA-INSTALL-$VERSION
    mv ncpa NCPA-INSTALL-$VERSION/ncpa
    cp NCPA-INSTALL-$VERSION/ncpa/build_resources/macosuninstall.sh NCPA-INSTALL-$VERSION/ncpa/uninstall.sh
    mv NCPA-INSTALL-$VERSION/ncpa/build_resources/macosinstall.sh NCPA-INSTALL-$VERSION/install.sh
    install_name_tool -change /Library/Frameworks/Python.framework/Versions/2.7/Python @executable_path/Python NCPA-INSTALL-$VERSION/ncpa/ncpa_listener
    install_name_tool -change /Library/Frameworks/Python.framework/Versions/2.7/Python @executable_path/Python NCPA-INSTALL-$VERSION/ncpa/ncpa_passive
    hdiutil create -volname NCPA-$VERSION -srcfolder NCPA-INSTALL-$VERSION -ov -format UDZO ncpa-$VERSION.dmg
)
