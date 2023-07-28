#!/usr/bin/env bash

echo -e "\n***** macos/package.sh"

# Get version
DIR=$( cd "$(dirname "$0")" ; pwd -P )
BUILD_DIR="$DIR/.."
NCPA_VER=$(cat $BUILD_DIR/../VERSION)
RELEASE="beta02"
ARCH=$(arch)

(
    echo -e "***** macos/package.sh - fix dylib dependencies"
    # Make some dylib dependency paths relative so they will work on target machine
    install_name_tool -change /usr/local/Cellar/openssl@3/3.1.1_1/lib/libcrypto.3.dylib @loader_path/libcrypto.3.dylib ncpa-$NCPA_VER/lib/libssl.3.dylib
    install_name_tool -change /usr/local/opt/openssl@3/lib/libssl.3.dylib @loader_path/libssl.3.dylib ncpa-$NCPA_VER/lib/_ssl.cpython-311-darwin.so
    install_name_tool -change /usr/local/opt/openssl@3/lib/libcrypto.3.dylib @loader_path/libcrypto.3.dylib ncpa-$NCPA_VER/lib/_ssl.cpython-311-darwin.so

    # Uncomment otool comands to have updated dynamic lib dependencies dispayed
    # otool -L ncpa-$NCPA_VER/lib/libssl.3.dylib
    # otool -L ncpa-$NCPA_VER/lib/_ssl.cpython-311-darwin.so

    echo -e "\n***** macos/package.sh - copy other resources"
    mkdir NCPA-INSTALL-$NCPA_VER
    mv ncpa-$NCPA_VER NCPA-INSTALL-$NCPA_VER/ncpa
    cp NCPA-INSTALL-$NCPA_VER/ncpa/build_resources/macosuninstall.sh NCPA-INSTALL-$NCPA_VER/ncpa/uninstall.sh
    cp NCPA-INSTALL-$NCPA_VER/ncpa/build_resources/macosreadme.txt NCPA-INSTALL-$NCPA_VER/readme.txt
    mv NCPA-INSTALL-$NCPA_VER/ncpa/build_resources/macosinstall.sh NCPA-INSTALL-$NCPA_VER/install.sh

    # Create MacOS disk image file
    echo -e "\n***** macos/package.sh - creating .dmg file ..."
    RELEASE=$RELEASE"_"
    hdiutil create -volname NCPA-$NCPA_VER -srcfolder NCPA-INSTALL-$NCPA_VER -ov -format UDZO ncpa_$NCPA_VER-$RELEASE$ARCH.dmg
)
