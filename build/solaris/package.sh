#!/bin/bash

# Get version
DIR=$(dirname "$(readlink -f "$0")")
VERSION=$(cat ../../VERSION)

# Set up package info
ARCH=$(arch)
sed "s/ARCH=.*/ARCH=$ARCH/" pkginfo > pkginfo.tmp
mv pkginfo.tmp ../pkginfo

# Make the package and cleanup
(
    cd ..
    cp pkginfo ncpa/pkginfo

    # Add prototype file
    echo 'i pkginfo' > prototype
    pkgproto ncpa >> /prototype

    # Build package and create the .pkg file
    pkgmk -b $(pwd) -o
    pkgtrans -s /var/spool/pkg ncpa-$VERSION.$ARCH.pkg ncpa

    # Remove build leftovers
    rm -rf /var/spool/pkg/ncpa
    rm -rf ncpa
    rm -f prototype
    rm -f pkginfo
)
