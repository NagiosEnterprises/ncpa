#!/usr/bin/env bash
echo " "
echo "Functions: get_distro, install_devtools, install_zlib, install_openssl, install_ssl_and_zlib"
echo " "
echo "To do full update, enter: install_ssl_and_zlib"
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

        # Update pkg repo file - deb9 apt sources are no longer valid. This is solved by deb8 installer, but not deb9.
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

# Can take a zLib version number as arg
install_zlib() {
    local zLib_new_version="1.2.13"
    echo -e " "
    echo -e " "
    echo -e "********************************************"
    echo -e "Building zLib $zLib_new_version..."
    echo -e " "

    if [[ ! -z $1 ]]; then
        zLib_new_version=$1
    fi

    pushd /usr/src
    wget https://zlib.net/zlib-$zLib_new_version.tar.gz --no-check-certificate
    tar -zxf zlib-$zLib_new_version.tar.gz

    pushd zlib-$zLib_new_version
    ./configure --64
    make && make test && make install
    popd

    local libz=$(find "/usr" -name "libz.so*" | grep -v "/src" | grep $zLib_new_version | head -n 1)
    echo -e " "
    echo -e " "
    echo -e "********************************************"

    if [[ ! -z $libz ]]; then
        rm -rf zlib-$zLib_new_version
        echo -e "SUCCESS! zLib $zLib_new_version is installed @ $libz"
        echo -e "********************************************"
        echo -e " "
        echo -e " "
        return 0
    else
        echo -e "ERROR! zLib $zLib_new_version failed to install correctly"
        echo -e "********************************************"
        echo -e " "
        echo -e " "
        return 1
    fi
}

# Can take an OpenSSL version number as arg
install_openssl() {
    local ssl_new_version="3.0.8"
    local ssl3_path="/usr/local/ssl3"

    echo -e " "
    echo -e " "
    echo -e "********************************************"
    echo -e "Building OpenSSL $ssl_new_version..."
    echo -e " "

    if [[ ! -z $1 ]]; then
        ssl_new_version=$1
    fi

    local ssl_old_path=$(dirname $(dirname $(which openssl)))
    local ssl_old_lib=$(dirname $(find /usr -name "libssl.so*" | grep -v /src | head -n1))
    local my_distro=$(get_distro)

    echo -e " "
    echo "ssl3_path: $ssl3_path, ssl_old_path: $ssl_old_path, ssl_old_lib: $ssl_old_lib"
    echo -e " "

    pushd /usr/src

    wget https://www.openssl.org/source/openssl-$ssl_new_version.tar.gz --no-check-certificate
    tar -zxf openssl-$ssl_new_version.tar.gz

    pushd openssl-$ssl_new_version
    ./config --prefix=$ssl3_path
    make all && make test && make install
    popd

    if [[ "$my_distro" == "debian"* ]] || [[ "$my_distro" == "ubuntu"* ]]; then
        if [[ -f "$ssl_old_lib/libssl.so" ]]; then
            mv $ssl_old_lib/libssl.so $ssl_old_lib/libssl.so.bak
        fi
        ln -s $ssl3_path/lib64/libssl.so $ssl_old_lib/libssl.so
        ln -s $ssl3_path/lib64/libssl.so.3 $ssl_old_lib/libssl.so.3
        ln -s $ssl3_path/lib64/libcrypto.so.3 $ssl_old_lib/libcrypto.so.3
    fi

    local sslchk=$($ssl_path/bin/openssl version | grep $ssl_new_version)
    echo -e " "
    echo -e " "
    echo -e "********************************************"

    if [[ ! -z $sslchk ]]; then
        PATH=$ssl3_path:$PATH
        rm -rf openssl-$ssl_new_version
        echo -e "SUCCESS! OpenSSL $ssl_new_version is installed"
        echo -e "********************************************"
        echo -e " "
        echo -e " "
        return 0
    else
        echo -e "ERROR! OpenSSL $ssl_new_version failed to install correctly"
        echo -e "********************************************"
        echo -e " "
        echo -e " "
        return 1
    fi
}

# Can take a Python version number as arg
install_python() {
    local python_new_version="3.11.3"
    local ssl3_path="/usr/local/ssl3"
    if [[ ! -z "$1" ]]; then
        python_new_version="$1"
    fi
    local pythontar="Python-$python_new_version"

    if [ ! -f $pythontar.tgz ]; then
        wget https://www.python.org/ftp/python/$python_new_version/$pythontar.tgz
    fi
    tar xf $pythontar.tgz
    cd $pythontar
    #./configure  --with-openssl=$ssl3_path --with-openssl-rpath=auto && \
    ./configure  --with-openssl=$ssl3_path && \
    make && make altinstall
    cd ..
    #rm -rf $pythontar
}

# Can take an OpenSSL version and a zLib verions number number as args
install_ssl_and_zlib() {
    local ssl_new_version="3.0.8"
    local zLib_new_version="1.2.13"

    if [[ ! -z "$1" ]]; then
        ssl_new_version="$1"
    fi

    if [[ ! -z "$2" ]]; then
        zLib_new_version="$2"
    fi

    curr_ver_int=$(get_sslver)
    new_ver_int=$(echo "$ssl_new_version"  | sed 's/\.//g')

    if (( "$new_ver_int" > "$curr_ver_int" )); then
        echo -e "Updating zLib and OpenSSL..."

        install_devtools && \
        install_zlib $zLib_new_version && \
        install_openssl $ssl_new_version

        return 0
    else
        echo "Current OpenSSL is as good or better. Nothing changed."
        return 0
    fi
}

# Requires globals $PYTHONBIN and $BUILD_DIR
update_py_packages() {
    echo -e "***** linux/setup.sh - update_py_packages()"
    $PYTHONBIN -m pip install --upgrade pip
    $PYTHONBIN -m pip install -r $BUILD_DIR/resources/require.txt --upgrade
}
