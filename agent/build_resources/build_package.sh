if [ "$1" == "rpm" ];
then
    cp build_resources/postinstall-pak .
    cp build_resources/postremove-pak .
    cp build_resources/description-pak .
    checkinstall    --pkgname=ncpa \
                    --strip=no \
                    --stripso=no \
                    --exclude=/var,/dev,/tmp \
                    --nodoc \
                    -R \
                    cp build/exe.linux-i686-2.6 /usr/local/ncpa -r
elif [ "$1" == "pkg" ];
then
    echo "Moving deb installs to current dir..."
    cp build_resources/postinstall-pak-deb postinstall-pak
    cp build_resources/postremove-pak-deb postremove-pak
    cp build_resources/description-pak .
    mv build/exe.linux-i686-2.6 build/ncpa
    checkinstall    --pkgname=ncpa \
                    --strip=no \
                    --stripso=no \
                    --exclude=/var,/dev,/tmp \
                    --nodoc \
                    -D \
                    cp build/ncpa /usr/local/ -r
fi
