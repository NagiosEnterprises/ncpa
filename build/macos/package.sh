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

    # Removed all OpenSSL-related entries from fixlibs and any code that attempts to fix or reference OpenSSL libraries.

    # Uncomment otool commands to have updated dynamic lib dependencies displayed
    echo -e "\n\n    Dependencies updated to use @loader_path:"
    find "$NCPAdir/lib" -maxdepth 1 -type f -exec otool -L {} + | grep "loader"
    echo -e "\nDone"

    # cx_Freeze edits load paths with install_name_tool but only re-signs on arm64,
    # and dyld on older macOS refuses to load a Mach-O file whose signature no longer
    # matches it ("code signature does not cover entire file up to signature").
    echo -e "\n    Applying ad-hoc code signatures..."
    find "$NCPAdir" -type f | while IFS= read -r f; do
        if file -b "$f" | grep -q "Mach-O"; then
            sudo codesign --force --sign - "$f" || echo "    WARNING: could not sign $f"
        fi
    done
    sudo codesign --verify --strict "$NCPAdir/ncpa" "$NCPAdir/lib/Python" || echo "    WARNING: code signature verification failed"

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
