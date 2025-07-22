#!/bin/bash

# Get version and architecture
if command -v realpath >/dev/null 2>&1; then
    realpath_cmd="realpath"
elif command -v grealpath >/dev/null 2>&1; then
    realpath_cmd="grealpath"
else
    echo "ERROR: Neither realpath nor grealpath command found."
    echo "Please install GNU coreutils or ensure realpath is available."
    exit 1
fi

DIR=$(dirname "$(readlink -f "$0")")
BUILD_DIR=$($realpath_cmd "$DIR/..")
VERSION=$(cat $BUILD_DIR/../VERSION)
ARCH=$(arch)

echo "Building Solaris package for NCPA version $VERSION on $ARCH architecture"

# Set up package info - fix the sed commands
echo "Setting up package information..."
sed "s/VERSION=.*/VERSION=$VERSION/" $DIR/pkginfo > $DIR/pkginfo.tmp
sed "s/ARCH=.*/ARCH=$ARCH/" $DIR/pkginfo.tmp > $BUILD_DIR/pkginfo
rm -rf $DIR/pkginfo.tmp

# Make the package and cleanup
(
    cd $BUILD_DIR

    echo "Cleaning up old packages..."
    rm -f ncpa*.pkg

    echo "Preparing package files..."
    # Add package information/scripts to pkg base
    cp pkginfo ncpa/pkginfo
    cp solaris/postinstall ncpa/postinstall
    cp solaris/preinstall ncpa/preinstall  
    cp solaris/preremove ncpa/preremove

    echo "Creating prototype file..."
    # Add prototype file
    echo 'i pkginfo' > prototype
    echo 'i postinstall' >> prototype
    echo 'i preinstall' >> prototype
    echo 'i preremove' >> prototype
    
    # Generate file list for the package
    echo "Generating file list..."
    if command -v pkgproto >/dev/null 2>&1; then
        pkgproto ncpa >> prototype
    else
        echo "ERROR: pkgproto command not found."
        echo "Please ensure Solaris packaging tools are installed."
        exit 1
    fi

    echo "Building package..."
    # Build package and create the .pkg file
    if command -v pkgmk >/dev/null 2>&1; then
        pkgmk -o -b $(pwd)
    else
        echo "ERROR: pkgmk command not found."
        echo "Please ensure Solaris packaging tools are installed."
        exit 1
    fi
    
    if command -v pkgtrans >/dev/null 2>&1; then
        pkgtrans -s /var/spool/pkg ncpa-$VERSION.$ARCH.pkg ncpa
        mv -f /var/spool/pkg/ncpa-$VERSION.$ARCH.pkg .
    else
        echo "ERROR: pkgtrans command not found."
        echo "Please ensure Solaris packaging tools are installed."
        exit 1
    fi

    echo "Cleaning up build artifacts..."
    # Remove build leftovers
    rm -rf /var/spool/pkg/ncpa
    rm -f prototype
    rm -f pkginfo
    rm -f ncpa/postinstall
    rm -f ncpa/preinstall
    rm -f ncpa/preremove

    echo "Package created successfully: ncpa-$VERSION.$ARCH.pkg"
)
