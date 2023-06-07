#!/usr/bin/env bash

# Scripts to install zLib, OpenSSL and Python, and update python libraries
#
# Functions: get_distro, get_sslver, install_devtools, install_zlib, install_openssl,
#            install_python, install_ssl_and_zlib, update_py_packages
#
# install_ssl_and_zlib installs both items.

#Returns distibution in form like "ubuntu22, or "centos9"
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

# Installs tools needed to make and install OpenSSL, zLib, and Python
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

    elif [[ "$my_distro" == "centos"* ]] || [[ "$my_distro" == "rhel"* ]] || [[ "$distro" == "Oracle" ]] || [[ "$distro" == "CloudLinux" ]]; then
        yum -y update
        yum -y install gcc gcc-c++ make perl-core perl-IPC-Cmd perl-Test-Simple perl-Pod-Html wget

    elif [[ "$my_distro" == "suse"* ]] || [[ "$my_distro" == "sles" ]] || [[ "$my_distro" == "opensuse"* ]]; then
        zypper -n update
        zypper -n install gcc gcc-c++ make perl-IPC-Cmd perl-Test-Simple wget
    fi
}

# Installs zLib from source.
# Requires a zLib version number, e.g. 1.2.13, as arg
install_zlib() {
    local zLib_new_version="1.2.13"

    if [[ ! -z $1 ]]; then
        zLib_new_version=$1
    else
        echo -e "ERROR! install_zlib() - No zLib version provided!"
        echo -e "********************************************\n\n"
        return 1
    fi
    echo -e "\n\n********************************************"
    echo -e "Building zLib $zLib_new_version...\n"

    pushd /usr/src
    wget https://zlib.net/zlib-$zLib_new_version.tar.gz --no-check-certificate
    tar -zxf zlib-$zLib_new_version.tar.gz

    pushd zlib-$zLib_new_version
    ./configure --64
    make && make test && make install
    popd

    local libz=$(find "/usr" -name "libz.so*" | grep -v "/src" | grep $zLib_new_version | head -n 1)
    echo -e "\n\n********************************************"

    if [[ ! -z $libz ]]; then
        rm -rf zlib-$zLib_new_version
        echo -e "SUCCESS! zLib $zLib_new_version is installed @ $libz"
        echo -e "********************************************\n\n"
        return 0
    else
        echo -e "ERROR! zLib $zLib_new_version failed to install correctly"
        echo -e "********************************************\n\n"
        return 1
    fi
}

# Installs OpenSSL from source
# Requires a OpenSSL version number, e.g. 3.0.8, as arg
install_openssl() {
    local ssl_new_version=""
    local ssl_new_path=""
    local ssl_new_base_path="/usr/local"

    if [[ ! -z $1 ]]; then
        ssl_new_version=$1
    else
        echo -e "ERROR! install_openssl() - No OpenSSL version provided!"
        echo -e "********************************************\n\n"
        return 1
    fi

    local new_ver_int=$(echo "$ssl_new_version"  | sed 's/\.//g')
    # ssl_new_path="$ssl_new_base_path/ssl$new_ver_int"
    ssl_new_path="$ssl_new_base_path/openssl"
    SSL_NEW_PATH=$ssl_new_path

    echo -e "\n\n********************************************"
    echo -e "Building OpenSSL $ssl_new_version at $ssl_new_path..."
    echo -e " "

    local ssl_old_path=$(dirname $(dirname $(which openssl)))
    local oldlib=$(find /usr -name "libssl.so*" | grep -v /src | head -n1)
    if [[ -z "$oldlib" ]]; then
        oldlib=$(find /lib -name "libssl.so*" | grep -v /src | head -n1)
    fi
    local ssl_old_lib=$(dirname $oldlib)
    local my_distro=$(get_distro)

    echo -e "\nssl_new_path: $ssl_new_path, ssl_old_path: $ssl_old_path, ssl_old_lib: $ssl_old_lib\n"

    pushd /usr/src

    wget https://www.openssl.org/source/openssl-$ssl_new_version.tar.gz --no-check-certificate
    tar -zxf openssl-$ssl_new_version.tar.gz

    pushd openssl-$ssl_new_version
    ./config --prefix=$ssl_new_path
    make all && make test && make install
    popd

    #If lib path hasn't changed then we don't need to link the new libraries. TODO confirm this.
    if [[ "$ssl_old_lib" != "$ssl_new_path/lib64" ]]; then
        if [[ -f "$ssl_old_lib/libssl.so" ]]; then
            mv $ssl_old_lib/libssl.so $ssl_old_lib/libssl.so.bak
            mv $ssl_old_lib/libcrypto.so $ssl_old_lib/libcrypto.so.bak
        fi
        ln -s $ssl_new_path/lib64/libssl.so $ssl_old_lib/libssl.so
        ln -s $ssl_new_path/lib64/libcrypto.so $ssl_old_lib/libcrypto.so

        if [[ -f "$ssl_old_lib/libssl.so.3" ]]; then
            mv $ssl_old_lib/libssl.so.3 $ssl_old_lib/libssl.so.3.bak
            mv $ssl_old_lib/libcrypto.so.3 $ssl_old_lib/libcrypto.so.3.bak
        fi
        ln -s $ssl_new_path/lib64/libssl.so.3 $ssl_old_lib/libssl.so.3
        ln -s $ssl_new_path/lib64/libcrypto.so.3 $ssl_old_lib/libcrypto.so.3
    fi

    echo -e "\nlibssl under /usr:"
    find "/usr" -name "libssl.so*" | grep -v /src
    echo -e "\nold lib ($ssl_old_lib) links :"
    ls -al $ssl_old_lib | grep -E "lib(ssl|crypto)"

    popd

    local sslchk=$($ssl_new_path/bin/openssl version | grep $ssl_new_version)
    echo -e "\nsslchk: $sslchk"
    echo -e "\n\n********************************************"

    if [[ ! -z $sslchk ]]; then
        echo -e "Before PATH: $PATH"
        PATH="$ssl_new_path/bin:$PATH"
        echo -e "After PATH: $PATH"

        rm -rf openssl-$ssl_new_version
        echo -e "SUCCESS! OpenSSL $ssl_new_version is installed"
        echo -e "********************************************\n\n"
        return 0
    else
        echo -e "ERROR! OpenSSL $ssl_new_version failed to install correctly"
        echo -e "********************************************\n\n"
        return 1
    fi
}

# Can take a Python version number as arg, otherwise uses default
# Can take an OpenSSL version number as a 2nd arg, otherwise uses existing OpenSSL
install_python() {
    local python_new_version=""
    local ssl_new_path=""

    if [[ ! -z $1 ]]; then
        python_new_version=$1
    else
        if [[ ! -z $PYTHONVER ]]; then
            python_new_version=$PYTHONVER
        else
            echo -e "ERROR! install_python() - No Python version provided!"
            echo -e "********************************************\n\n"
            return 1
        fi
    fi

    # SSL path global generated by install_openssl(). If it is empty, use default OpenSSL.
    # It can be provided as second arg if you want to run as stand-alone.
    if [[ ! -z "$2" ]]; then
        ssl_new_path="$2"
    else
        if [[ ! -z "$SSL_NEW_PATH" ]]; then
            ssl_new_path="$SSL_NEW_PATH"
        fi
    fi

    echo -e "\n\n********************************************"
    echo -e "Building Python $python_new_version...\n"

    local pythontar="Python-$python_new_version"

    if [ ! -f $pythontar.tgz ]; then
        wget https://www.python.org/ftp/python/$python_new_version/$pythontar.tgz
    fi
    tar xf $pythontar.tgz
    cd $pythontar
    echo -e " "
    if [[ -z $ssl_new_path ]]; then
        echo -e "Configure Python with default OpenSSL path"
        ./configure && \
        make && \
        make altinstall
    else
        echo -e "Configure Python with custom OpenSSL path: $ssl_new_path"
        ./configure  --with-openssl=$ssl_new_path && \
        make && \
        make altinstall
    fi
    echo -e " "
    cd ..
    #rm -rf $pythontar
}

# Can take an OpenSSL version and a zLib verions number number as args
install_ssl_and_zlib() {
    local ssl_new_version=""
    local zLib_new_version=""

    if [[ ! -z $1 ]]; then
        ssl_new_version=$1
    else
        if [[ ! -z $SSLVER ]]; then
            ssl_new_version=$SSLVER
        else
            echo -e "ERROR! install_ssl_and_zlib() - No OpenSSL version provided!"
            echo -e "********************************************\n\n"
            return 1
        fi
    fi

    if [[ ! -z $2 ]]; then
        zLib_new_version=$2
    else
        if [[ ! -z $ZLIBVER ]]; then
            zLib_new_version=$ZLIBVER
        else
            echo -e "ERROR! install_ssl_and_zlib() - No zLib version provided!"
            echo -e "********************************************\n\n"
            return 1
        fi
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
    echo -e "***** linux/installers.sh - update_py_packages()"
    $PYTHONBIN -m pip install --upgrade pip
    $PYTHONBIN -m pip install -r $BUILD_DIR/resources/require.txt --upgrade

    # cx freeze doesn't grab the proper _sslxxx.so and other libs, so we copy in the real ones.
    pylibpath=$(echo $PYTHONBIN | sed 's/bin/lib/g')
    echo -e "***** linux/installers.sh - update_py_packages() - copy $pylibpath/lib-dynload to cx_freeze lib-dynload"

    if [ ! -d "$pylibpath/site-packages/cx_Freeze/bases/lib-dynload_orig" ]; then
        mkdir $pylibpath/site-packages/cx_Freeze/bases/lib-dynload_orig
    fi
    cp $pylibpath/site-packages/cx_Freeze/bases/lib-dynload/* $pylibpath/site-packages/cx_Freeze/bases/lib-dynload_orig/

    # Link python's lib-dynload to cx_freeze lib-dynload to make sure we are using desired OpenSSL, etc.
    cp $pylibpath/lib-dynload/* $pylibpath/site-packages/cx_Freeze/bases/lib-dynload/
}
