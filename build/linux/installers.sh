#!/usr/bin/env bash
echo " "
echo "Functions: get_distro, install_devtools, install_zlib, install_openssl, update_ssl"
echo " "
echo "To do full update, enter: update_ssl"
echo " "


get_distro() {
    if [ -f "/etc/os-release" ]; then
        source /etc/os-release
        local myDistro="$ID$VERSION_ID "
    fi
    echo $myDistro
}

# Returns OpenSSL version as an integer, e.g., v1.1.1f -> 111, v3.0.8 -> 308 for easy comparison
get_sslver() {
    local ssl_ver=$(openssl version | grep -e "[1-3].[0-9].[0-9]" -o | head -n1 | sed 's/\.//g')
    echo $ssl_ver
    return 0
}

install_devtools() {
    local my_distro=$(get_distro)
    if [[ "$my_distro" == "debian"* ]] || [[ "$my_distro" == "ubuntu"* ]]; then

        # deb9 apt sources are no longer valid. This is solved by deb8 installer, but not deb9.
        if [[ "$my_distro" == "debian9" ]]; then
            mv /etc/apt/sources.list /etc/apt/sources.list.orig
            echo "deb http://archive.debian.org/debian/ stretch  main contrib non-free" >> /etc/apt/sources.list
            echo "deb http://security.debian.org/ stretch/updates main contrib non-free" >> /etc/apt/sources.list
            cat /etc/apt/sources.list
        fi
        apt-get -y update
        apt-get -y install build-essential perl libipc-run-perl libtest-simple-perl wget --allow-unauthenticated
    else
        yum -y update
        yum -y install gcc gcc-c++ make perl-core perl-IPC-Cmd perl-Test-Simple perl-Pod-Html wget
    fi
}

install_zlib() {
    local zLib_new_version="1.2.13"
    if [[ ! -z $1 ]]; then
        zLib_new_version=$1
    fi

    echo -e "Building zLib $zLib_new_version..."
    pushd /usr/src
    wget https://zlib.net/zlib-$zLib_new_version.tar.gz --no-check-certificate
    tar -zxf zlib-$zLib_new_version.tar.gz
    rm zlib-$zLib_new_version.tar.gz
    cd zlib-$zLib_new_version
    ./configure --64
    make && make test && make install

    local libz=$(find "/usr" -name "libz.so*" | grep -v "/src" | grep $zLib_new_version | head -n 1)

    popd
    if [[ ! -z $libz ]]; then
        echo -e "SUCCESS! zLib $zLib_new_version is installed @ $libz"
        echo -e " "
        return 0
    else
        echo -e "ERROR! zLib $zLib_new_version failed to install correctly"
        echo -e " "
        return 1
    fi
}

install_openssl() {
    local ssl_new_version="3.0.8"
    if [[ ! -z $1 ]]; then
        ssl_new_version=$1
    fi

    echo -e "Building OpenSSL $ssl_new_version..."
    pushd /usr/src
    local my_distro=$(get_distro)

    wget https://www.openssl.org/source/openssl-$ssl_new_version.tar.gz --no-check-certificate
    tar -zxf openssl-$ssl_new_version.tar.gz
    rm openssl-$ssl_new_version.tar.gz
    cd openssl-$ssl_new_version
    ./config --prefix=/usr
    make all && make test && make install

    if [[ "$my_distro" == "debian"* ]] || [[ "$my_distro" == "ubuntu"* ]]; then
        ln -s /usr/lib64/libssl.so.3 /lib/x86_64-linux-gnu/libssl.so.3
        ln -s /usr/lib64/libcrypto.so.3 /lib/x86_64-linux-gnu/libcrypto.so.3
    fi

    local sslchk=$(openssl version | grep $ssl_new_version)

    popd
    if [[ ! -z $sslchk ]]; then
        echo -e "SUCCESS! OpenSSL $ssl_new_version is installed"
        echo -e " "
        return 0
    else
        echo -e "ERROR! OpenSSL $ssl_new_version filed to install correctly"
        echo -e " "
        return 1
    fi
}

update_ssl() {
    local ssl_new_version="3.0.8"
    local zLib_new_version="1.2.13"

    if [[ ! -z "$1" ]]; then
        ssl_new_version="$1"
    fi

    curr_ver_int=$(get_sslver)
    new_ver_int=$(echo "$ssl_new_version"  | sed 's/\.//g')

    if (( "$new_ver_int" > "$curr_ver_int" )); then
        echo -e "Updating zLib and OpenSSL..."

        install_devtools && \
        install_zlib $zLib_new_version && \
        install_openssl $ssl_new_version

    else
        echo "Current OpenSSL is as good or better. Nothing changed."
    fi
}
