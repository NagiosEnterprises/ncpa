#!/bin/bash

# Get version
realpath=$(which realpath)
if [ ! -f $realpath ]; then
    realpath=$(which grealpath)
fi
DIR=$(dirname "$(readlink -f "$0")")
BUILD_DIR=$($realpath "$DIR/..")
VERSION=$(cat $BUILD_DIR/../VERSION)
ARCH=$(arch)

# Set up package info
sed "s/VERSION=.*/ARCH=$VERSION/" $DIR/pkginfo > $DIR/pkginfo.tmp
sed "s/ARCH=.*/ARCH=$ARCH/" $DIR/pkginfo.tmp > $BUILD_DIR/pkginfo
rm -rf $DIR/pkginfo.tmp

# Check version of Solaris
SOLARIS=11
if grep "Solaris 10" /etc/release > /dev/null ; then
    SOLARIS=10
fi

# Make the package and cleanup
(
    cd $BUILD_DIR

    # Clean up old package
    rm -f ncpa*.pkg

    # Add package information/scripts to pkg base
    cp pkginfo ncpa/pkginfo
    cp solaris/postinstall postinstall
    cp solaris/preinstall preinstall
    cp solaris/preremove preremove

    if [ $SOLARIS -eq 10 ]; then
        cp solaris/ncpa_listener.xml ncpa/ncpa_listener.xml
        cp solaris/ncpa_passive.xml ncpa/ncpa_passive.xml
    fi

    # Add prototype file
    echo 'i pkginfo' > prototype
    echo 'i postinstall' >> prototype
    echo 'i preinstall' >> prototype
    echo 'i preremove' >> prototype
    pkgproto ncpa >> prototype

    # Build package and create the .pkg file
    pkgmk -b $(pwd) -o
    pkgtrans -s /var/spool/pkg ncpa-$VERSION.$ARCH.pkg ncpa
    mv -f /var/spool/pkg/ncpa-$VERSION.$ARCH.pkg .

    # Remove build leftovers
    rm -rf /var/spool/pkg/ncpa
    rm -f prototype
    rm -f pkginfo
    rm -f postinstall
    rm -f preinstall
    rm -f preremove
)
