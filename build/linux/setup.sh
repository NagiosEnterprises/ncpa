#!/bin/bash

# Globals
PYTHONTAR="Python-2.7.14"
PYTHONVER="python2.7"
PYTHONBIN="/usr/local/bin/python2.7"
CXFREEZEVER="cx_Freeze-4.3.4"

# Get information about system
$BUILD_DIR/linux/init.sh

update_py_packages() {
    $PYTHONBIN -m pip install -r $BUILD_DIR/resources/require.txt --upgrade
}

install_prereqs() {


    # --------------------------
    #  INSTALL SYSTEM REQS
    # --------------------------


    if [ "$distro" == "Debian" ] || [ "$distro" == "Ubuntu" ]; then
        apt-get install debian-builder rpm gcc gcc-c++ git wget openssl libssl-dev libffi-dev sqlite3 libsqlite3-dev zlib1g-dev alien -y
    elif [ "$distro" == "CentOS" ] || [ "$distro" == "RHEL" ] || [ "$distro" == "Oracle" ] || [ "$distro" == "CloudLinux" ]; then
        yum install epel-release -y
        yum install gcc gcc-c++ zlib zlib-devel openssl openssl-devel rpm-build libffi-devel sqlite sqlite-devel wget -y
    elif [ "$distro" == "SUSE LINUX" ]; then
        zypper isntall gcc
    else
        echo "Could not determine your OS type... you need to install the following dependencies:"
        echo ""
        echo "gcc, gcc-c++"
        echo "zlib, zlib-devel"
        echo "openssl, openssl-devel"
        echo "sqlite3, sqlite3-devel"
        echo "libffi-devel"
        echo "rpm-build"
        echo "wget"
        echo "git"
        echo ""
        echo "If you're running a debian distro you must also install debian-builder"
        echo ""
        exit 1
    fi


    # --------------------------
    #  INSTALL SOURCE FILES
    # --------------------------


    cd $BUILD_DIR/resources

    # Install bundled Python version from source
    tar xf $PYTHONTAR.tgz
    cd $PYTHONTAR
    ./configure --with-zlib=/usr/include --enable-shared && make && make altinstall
    echo '/usr/local/lib' >> /etc/ld.so.conf 
    /sbin/ldconfig
    cd ..
    rm -rf $PYTHONTAR

    # Install the patched version of cx_Freeze
    tar xf $CXFREEZEVER.tar.gz
    cd $CXFREEZEVER
    $PYTHONBIN setup.py install
    cd ..
    rm -rf $CXFREEZEVER


    # --------------------------
    #  INSTALL PIP & PIP MODULES
    # --------------------------


    # Install pip
    cd /tmp && wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py && $PYTHONBIN /tmp/get-pip.py

    # Install modules
    $PYTHONBIN -m pip install -r $BUILD_DIR/resources/require.txt


    # --------------------------
    #  MISC ADDITIONS
    # --------------------------


    useradd nagios
    groupadd nagios
    usermod -g nagios nagios


}
