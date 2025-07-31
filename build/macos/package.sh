#!/usr/bin/env bash

echo -e "\n***** macos/package.sh"

# Source version configuration
BUILD_DIR_FOR_VERSION=$(dirname "$(dirname "$0")")
source "$BUILD_DIR_FOR_VERSION/version_config.sh"

# Get version
DIR=$( cd "$(dirname "$0")" ; pwd -P )
BUILD_DIR="$DIR/.."
NCPA_VER=$(cat $BUILD_DIR/../VERSION)
RELEASE="1"
ARCH=$(uname -m)

(
    echo -e "    Fixing dylib dependencies..."
    # Make some dylib dependency paths relative so they will work on target machine
    NCPAdir="ncpa-$NCPA_VER"
    
    # Determine Python version for .so file names
    if [[ -n "$PYTHONVER" ]]; then
        py_major_minor=$(echo $PYTHONVER | sed 's/\.//')
    else
        # Fallback to detecting from built files
        py_major_minor=$(ls $NCPAdir/lib/_ssl.cpython-*-darwin.so 2>/dev/null | head -1 | sed 's/.*cpython-\([0-9]*\)-.*/\1/')
        if [[ -z "$py_major_minor" ]]; then
            py_major_minor="313"  # Default to 3.13
        fi
    fi
    
    echo "    Using Python version suffix: cpython-$py_major_minor"
    # otool -L $NCPAdir/lib/*

    # Add args for install_name_tool() in format:
    #     "oldlib1~newlib1~parentlib1 oldlib2~newlib2~parentlib2 etc....""
    fixlibs="\
    /usr/local/Cellar/openssl@${OPENSSL_MAJOR}/$SSLVER/lib/libcrypto.${LIBCRYPTO_VERSION}.dylib~@loader_path/libcrypto.${LIBCRYPTO_VERSION}.dylib~$NCPAdir/lib/libssl.${LIBSSL_VERSION}.dylib \
    /usr/local/opt/openssl@${OPENSSL_MAJOR}/lib/libssl.${LIBSSL_VERSION}.dylib~@loader_path/libssl.${LIBSSL_VERSION}.dylib~$NCPAdir/lib/_ssl.cpython-$py_major_minor-darwin.so \
    /usr/local/opt/openssl@${OPENSSL_MAJOR}/lib/libcrypto.${LIBCRYPTO_VERSION}.dylib~@loader_path/libcrypto.${LIBCRYPTO_VERSION}.dylib~$NCPAdir/lib/_ssl.cpython-$py_major_minor-darwin.so \
    /usr/lib/libsqlite3.dylib~@loader_path/libsqlite3.dylib~$NCPAdir/lib/_sqlite3.cpython-$py_major_minor-darwin.so \
    /usr/local/opt/sqlite/lib/libsqlite${SQLITE3_VERSION}.dylib~@loader_path/libsqlite${SQLITE3_VERSION}.dylib~$NCPAdir/lib/_sqlite3.cpython-$py_major_minor-darwin.so \
    /usr/local/opt/mpdecimal/lib/libmpdec.${MPDECIMAL_VERSION}.dylib~@loader_path/libmpdec.dylib~$NCPAdir/lib/_decimal.cpython-$py_major_minor-darwin.so \
    /usr/local/opt/openssl@${OPENSSL_MAJOR}/lib/libcrypto.${LIBCRYPTO_VERSION}.dylib~@loader_path/libcrypto.${LIBCRYPTO_VERSION}.dylib~$NCPAdir/lib/_hashlib.cpython-$py_major_minor-darwin.so \
    "

    if [[ "$os_major_version" == "10" ]]; then
        echo "    Fix libffi (MacOS v10.x only)"
        fixlibs="$fixlibs /usr/local/opt/libffi/lib/libffi.${LIBFFI_VERSION}.dylib~@loader_path/libffi.${LIBFFI_VERSION}.dylib~$NCPAdir/lib/_ctypes.cpython-$py_major_minor-darwin.so "
    fi

    # Convert string to array
    fixlibs=($fixlibs)

    for fixlib in "${fixlibs[@]}"
    do
        oldlib=$(echo ${fixlib} | cut -f1 -d~)
        newlib=$(echo ${fixlib} | cut -f2 -d~)
        parentlib=$(echo ${fixlib} | cut -f3 -d~)
        
        # Check if the target file exists before trying to modify it
        if [[ -f "$parentlib" ]]; then
            echo -e "\n    Fixing: $parentlib"
            echo "    $oldlib -> $newlib"
            sudo install_name_tool -change $oldlib $newlib $parentlib
        else
            echo -e "\n    Skipping: $parentlib (file not found)"
        fi
    done

    # Uncomment otool comands to have updated dynamic lib dependencies dispayed
    echo -e "\n\n    Dependencies updated to use @loader_path:"
    otool -L $NCPAdir/lib/* | grep "loader"
    echo -e "\nDone"

    echo -e "\nCopy other resources..."
    sudo mkdir NCPA-INSTALL-$NCPA_VER
    sudo mv ncpa-$NCPA_VER NCPA-INSTALL-$NCPA_VER/ncpa
    sudo cp NCPA-INSTALL-$NCPA_VER/ncpa/build_resources/macosuninstall.sh NCPA-INSTALL-$NCPA_VER/ncpa/uninstall.sh
    sudo cp NCPA-INSTALL-$NCPA_VER/ncpa/build_resources/macosreadme.txt NCPA-INSTALL-$NCPA_VER/readme.txt
    sudo mv NCPA-INSTALL-$NCPA_VER/ncpa/build_resources/macosinstall.sh NCPA-INSTALL-$NCPA_VER/install.sh

    # Create MacOS disk image file
    echo -e "\nCreate .dmg file ..."
    RELEASE=$RELEASE"_"
    sudo hdiutil create -volname NCPA-$NCPA_VER -srcfolder NCPA-INSTALL-$NCPA_VER -ov -format UDZO ncpa_$NCPA_VER-$RELEASE$ARCH.dmg
)
