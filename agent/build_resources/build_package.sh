if [ "$1" == "rpm" ] || [ "$2" == "rpm" ];
then
    cp build_resources/postinstall-pak .
    cp build_resources/postremove-pak .
    cp build_resources/description-pak .
    checkinstall    --pkgname=ncpa \
                    --strip=no \
                    --stripso=no \
                    --exclude=/var,/dev,/tmp \
                    --pakdir=. \
                    --nodoc \
                    -R \
                    cp build/exe.linux-i686-2.6 /usr/local/ncpa -r
fi

if [ "$1" == "pkg" ] || [ "$2" == "pkg" ];
then
    echo "Moving deb installs to current dir..."
    cp build_resources/postinstall-pak-deb postinstall-pak
    cp build_resources/postremove-pak-deb postremove-pak
    cp build_resources/description-pak .
    checkinstall    --pkgname=ncpa \
                    --install=no \
                    --strip=no \
                    --stripso=no \
                    --exclude=/var,/dev,/tmp \
                    --nodoc \
                    --pakdir=. \
                    -D \
                    cp build/exe.linux-i686-2.6 /usr/local/ncpa -r
fi
