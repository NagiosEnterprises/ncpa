if [ "$1" == "rpm" ];
then
    cp build_resources/postinstall-pak .
    cp build_resources/postremove-pak .
    cp build_resources/description-pak .
    checkinstall --pkgname=ncpa --strip=no --stripso=no --exclude=/var,/dev,/tmp --nodoc -R cp build/exe.linux-i686-2.6 /usr/local/ncpa -r
fi
