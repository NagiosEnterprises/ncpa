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
cat linux/ncpa.spec | sed "s/__VERSION__/$NCPA_VER/g" | sed "s|__BUILDROOT__|$BUILD_RPM_DIR|g" > $BUILD_DIR/ncpa.spec

# Build rpm package (also used on Debian systems)
echo -e "***** Build rpm package"
(
    if [[ -d $BUILD_RPM_DIR ]]; then
        echo -e "***** Remove old rpm package directories"
        rm -r $BUILD_RPM_DIR
    fi
    echo -e "***** Build rpm package - make directories"
    mkdir -p $BUILD_RPM_DIR/SPECS
    mkdir -p $BUILD_RPM_DIR/SRPMS
    mkdir -p $BUILD_RPM_DIR/RPMS
    mkdir -p $BUILD_RPM_DIR/SOURCES
    mkdir -p $BUILD_RPM_DIR/BUILD
    cp -f $BUILD_DIR/ncpa-$NCPA_VER.tar.gz $BUILD_RPM_DIR/SOURCES/
    rm -f $BUILD_RPM_DIR/SPECS/ncpa.spec
    cp -f $BUILD_DIR/ncpa.spec $BUILD_RPM_DIR/SPECS/

    echo -e "***** Build rpm package - rpmbuild"
    if [ "$distro" == "Raspbian" ]; then
        parch=`uname -m`
        QA_RPATHS='$[ 0x0002 ]' rpmbuild $BUILD_RPM_DIR/SPECS/ncpa.spec -bb --target=armhf --define "_topdir $BUILD_RPM_DIR" --define "_arch armhf" >> $BUILD_DIR/build.log
    else
        QA_RPATHS='$[ 0x0002 ]' rpmbuild $BUILD_RPM_DIR/SPECS/ncpa.spec -bb --define "_topdir $BUILD_RPM_DIR" >> $BUILD_DIR/build.log
    fi

    echo -e "***** Build rpm package - find RPMs and copy to build dir"
    find $BUILD_RPM_DIR/RPMS -name "ncpa-$NCPA_VER*" -exec cp {} . \;
)

dist_ver="notcentos7"
if [ "$distro" == "CentOS" ] && [ "$dist" == "el7" ]; then
    dist_ver="centos7"
fi

# Convert into a deb package for Debian systems
# CentOS 7 builds run on almost all linux variants and versions, so for
# production purposes, we always generate a .deb when building on CentOS 7, too

if [ "$distro" == "Debian" ] || [ "$distro" == "Ubuntu" ] || [ "$distro" == "Raspbian" ] || [ "$dist_ver" == "centos7" ]; then
    echo -e "***** Convert to .deb"

    echo -e "***** Convert to .deb - apt install alien"
    if [ "$dist_ver" == "centos7" ]; then
        yum install alien
    else
        apt-get install alien
    fi

    echo -e "***** Convert to .deb - mk debbuild dir"
    cd $BUILD_DIR
    mkdir -p debbuild
    cp *.rpm debbuild/
    ls -al
    cd debbuild

    # Create deb package with alien
    rpm="*.rpm "
    if [ "$distro" == "Raspbian" ]; then
        rpm="*armhf.rpm"
    fi

    echo -e "***** Convert to .deb - run alien"
    if [ "$architecture" == "aarch64" ]; then
      alien -c -k -v --target=arm64 $rpm >> $BUILD_DIR/build.log
    else
      alien -c -k -v $rpm >> $BUILD_DIR/build.log
    fi
    echo -e "***** Convert to .deb - alien done"

    cd $BUILD_DIR
    cp debbuild/*.deb .
    cp debbuild/*.rpm .

    if [ "$dist_ver" != "centos7" ]; then
        rm -rf *.rpm
    fi
    rm -rf debbuild
fi
