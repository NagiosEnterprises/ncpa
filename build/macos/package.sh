#!/usr/bin/env bash

echo -e "\n***** macos/package.sh"

# Get version
DIR=$( cd "$(dirname "$0")" ; pwd -P )
BUILD_DIR="$DIR/.."
NCPA_VER=$(cat $BUILD_DIR/../VERSION)
RELEASE="beta02"
ARCH=$(arch)

(
    echo -e "    - fix dylib dependencies"
    # Make some dylib dependency paths relative so they will work on target machine
    NCPAdir="ncpa-$NCPA_VER"
    echo "NCPAdir: $NCPAdir"
    sslver="3.1.2"
    otool -L $NCPAdir/lib/*

    fixlibs=(\
    "/usr/local/Cellar/openssl@3/$sslver/lib/libcrypto.3.dylib~@loader_path/libcrypto.3.dylib~$NCPAdir/lib/libssl.3.dylib" \
    "/usr/local/opt/openssl@3/lib/libssl.3.dylib~@loader_path/libssl.3.dylib~$NCPAdir/lib/_ssl.cpython-311-darwin.so" \
    "/usr/local/opt/openssl@3/lib/libcrypto.3.dylib~@loader_path/libcrypto.3.dylib~$NCPAdir/lib/_ssl.cpython-311-darwin.so" \
    "/usr/lib/libsqlite3.dylib~@loader_path/libsqlite3.dylib~$NCPAdir/lib/_sqlite3.cpython-311-darwin.so" \
    "/usr/local/opt/sqlite/lib/libsqlite3.0.dylib~@loader_path/libsqlite3.0.dylib~$NCPAdir/lib/_sqlite3.cpython-311-darwin.so" \
    "/usr/local/opt/mpdecimal/lib/libmpdec.3.dylib~@loader_path/libmpdec.dylib~$NCPAdir/lib/_decimal.cpython-311-darwin.so" \
    "/usr/local/opt/openssl@3/lib/libcrypto.3.dylib~@loader_path/libcrypto.3.dylib~$NCPAdir/lib/_hashlib.cpython-311-darwin.so" \
    )

    echo -e "\n\nFixing NCPA libs..."
    for fixlib in "${fixlibs[@]}"
    do
        oldlib=$(echo ${fixlib} | cut -f1 -d~)
        newlib=$(echo ${fixlib} | cut -f2 -d~)
        parentlib=$(echo ${fixlib} | cut -f3 -d~)
        echo -e "\nFixing: $parentlib"
        echo "    $oldlib -> $newlib"
        sudo install_name_tool -change $oldlib $newlib $parentlib
    done
    echo -e "\nDone\n\n"

    # Uncomment otool comands to have updated dynamic lib dependencies dispayed
    otool -L $NCPAdir/lib/* | grep -B1 "loader"
    # otool -L ncpa-$NCPA_VER/lib/_ssl.cpython-311-darwin.so

    echo -e "    - copy other resources"
    mkdir NCPA-INSTALL-$NCPA_VER
    mv ncpa-$NCPA_VER NCPA-INSTALL-$NCPA_VER/ncpa
    cp NCPA-INSTALL-$NCPA_VER/ncpa/build_resources/macosuninstall.sh NCPA-INSTALL-$NCPA_VER/ncpa/uninstall.sh
    cp NCPA-INSTALL-$NCPA_VER/ncpa/build_resources/macosreadme.txt NCPA-INSTALL-$NCPA_VER/readme.txt
    mv NCPA-INSTALL-$NCPA_VER/ncpa/build_resources/macosinstall.sh NCPA-INSTALL-$NCPA_VER/install.sh

    # Create MacOS disk image file
    echo -e "    - creating .dmg file ..."
    RELEASE=$RELEASE"_"
    hdiutil create -volname NCPA-$NCPA_VER -srcfolder NCPA-INSTALL-$NCPA_VER -ov -format UDZO ncpa_$NCPA_VER-$RELEASE$ARCH.dmg
)
