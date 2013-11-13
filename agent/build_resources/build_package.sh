#!/bin/bash

VERSION=`python2.6 -c 'import listener.server as a;print a.__VERSION__'`

if [ "$1" == "rpm" ] || [ "$2" == "rpm" ];
then
    cp build_resources/postinstall-pak .
    cp build_resources/postremove-pak .
    cp build_resources/description-pak .
    cp build_resources/NagiosSoftwareLicense.txt build/exe.linux-*/
    mv build/exe.linux-* build-pkg
    checkinstall    --pkgname=ncpa \
                    --install=no \
                    --strip=no \
                    --arch=`arch` \
                    --stripso=no \
                    --exclude=/var,/dev,/tmp \
                    --pkgversion="$VERSION" \
                    --pakdir=. \
                    --nodoc \
                    --maintainer=nscott@nagios.com \
                    --pkglicense='Nagios Open Source License' \
                    -R \
                    -y \
                    cp build-pkg/* /usr/local/ncpa -r
fi

if [ "$1" == "pkg" ] || [ "$2" == "pkg" ];
then
    echo "Moving deb installs to current dir..."
    cp build_resources/postinstall-pak-deb postinstall-pak
    cp build_resources/postremove-pak-deb postremove-pak
    cp build_resources/description-pak .
    cp build_resources/NagiosSoftwareLicense.txt build/exe.linux-*/
    checkinstall    --pkgname=ncpa \
                    --install=no \
                    --strip=no \
                    --arch=`arch` \
                    --maintainer=nscott@nagios.com \
                    --pkgversion="$VERSION" \
                    --pkglicense='Nagios Open Source License' \
                    --stripso=no \
                    --exclude=/var,/dev,/tmp \
                    --nodoc \
                    -D \
                    -y \
                    cp build/exe.linux-* /usr/local/ncpa -r
fi
