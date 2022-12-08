#!/bin/bash -e

echo -e "***** linux/package.sh"

# Set global build opts
DIR=$(dirname "$(readlink -f "$0")")
BUILD_DIR=$(readlink -f "$DIR/..")
BUILD_RPM_DIR="/usr/src/redhat"

# Get information about system
. $BUILD_DIR/linux/init.sh
NCPA_VER=$(cat $BUILD_DIR/../VERSION)

# Build spec file
echo -e "***** Build spec file"
cd $BUILD_DIR
sudo cat linux/ncpa.spec | sudo sed "s/__VERSION__/$NCPA_VER/g" | sudo sed "s|__BUILDROOT__|$BUILD_RPM_DIR|g" > $BUILD_DIR/ncpa.spec

# Build rpm package (also used on Debian systems)
echo -e "***** Build rpm package"
(
    echo -e "***** Build rpm package - make directories"
    sudo mkdir -p $BUILD_RPM_DIR/SPECS
    sudo mkdir -p $BUILD_RPM_DIR/SRPMS
    sudo mkdir -p $BUILD_RPM_DIR/RPMS
    sudo mkdir -p $BUILD_RPM_DIR/SOURCES
    sudo mkdir -p $BUILD_RPM_DIR/BUILD
    sudo cp -f $BUILD_DIR/ncpa-$NCPA_VER.tar.gz $BUILD_RPM_DIR/SOURCES/
    sudo rm -f $BUILD_RPM_DIR/SPECS/ncpa.spec
    sudo cp -f $BUILD_DIR/ncpa.spec $BUILD_RPM_DIR/SPECS/

    echo -e "***** Build rpm package - rpmbuild"
    if [ "$distro" == "Raspbian" ]; then
        parch=`uname -m`
        QA_RPATHS='$[ 0x0002 ]' sudo rpmbuild $BUILD_RPM_DIR/SPECS/ncpa.spec -bb --target=armhf --define "_topdir $BUILD_RPM_DIR" --define "_arch armhf" >> $BUILD_DIR/build.log
    else
        QA_RPATHS='$[ 0x0002 ]' sudo rpmbuild $BUILD_RPM_DIR/SPECS/ncpa.spec -bb --define "_topdir $BUILD_RPM_DIR" >> $BUILD_DIR/build.log
    fi

    echo -e "***** Build rpm package - find"
    sudo find $BUILD_RPM_DIR/RPMS -name "ncpa-$NCPA_VER*" -exec cp {} . \;
)

# Convert into a deb package for Debian systems
if [ "$distro" == "Debian" ] || [ "$distro" == "Ubuntu" ] || [ "$distro" == "Raspbian" ]; then
    echo -e "***** Convert to .deb"

    echo -e "***** Convert to .deb - apt install alien"
    sudo apt install alien

    echo -e "***** Convert to .deb - mk debbuild dir"
    cd $BUILD_DIR
    sudo mkdir -p debbuild
    sudo cp *.rpm debbuild/
    cd debbuild

    # Create deb package with alien
    rpm="*.rpm "
    if [ "$distro" == "Raspbian" ]; then
        rpm="*armhf.rpm"
    fi

    echo -e "***** Convert to .deb - run alien"
    if [ "$architecture" == "aarch64" ]; then
      sudo alien -c -k -v --target=arm64 $rpm >> $BUILD_DIR/build.log
    else
      sudo alien -c -k -v $rpm >> $BUILD_DIR/build.log
    fi
    echo -e "***** Convert to .deb - alien done"

    cd $BUILD_DIR
    sudo cp debbuild/*.deb .

    sudo rm -rf *.rpm
    sudo rm -rf debbuild
    ls -al

fi
