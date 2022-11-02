#!/bin/bash

echo -e "***** linux/setup.sh"

# Globals
PYTHONVER="3.9.13"
PYTHONTAR="Python-$PYTHONVER"
PYTHONBIN=$(which python3.9)
SKIP_PYTHON=0

# Get information about system
. $BUILD_DIR/linux/init.sh

update_py_packages() {
    # Removed from before PYTHONBIN: LDFLAGS='-Wl,-rpath,\${ORIGIN} -Wl,-rpath,\${ORIGIN}/lib'
    # Removed from end: --no-binary :all:
    $PYTHONBIN -m pip install --upgrade pip
    $PYTHONBIN -m pip install -r $BUILD_DIR/resources/require.txt --upgrade
}

install_prereqs() {


    # --------------------------
    #  INSTALL SYSTEM REQS
    # --------------------------


    if [ "$distro" == "Debian" ] || [ "$distro" == "Ubuntu" ]; then

        apt-get install debian-builder rpm gcc g++ wget openssl libssl-dev libffi-dev sqlite3 libsqlite3-dev zlib1g-dev alien -y

    elif [ "$distro" == "CentOS" ] || [ "$distro" == "RHEL" ] || [ "$distro" == "Oracle" ] || [ "$distro" == "CloudLinux" ]; then

        yum install epel-release -y
        yum install gcc gcc-c++ zlib zlib-devel openssl openssl-devel rpm-build libffi-devel sqlite sqlite-devel wget make -y

    elif [ "$distro" == "SUSE LINUX" ] || [ "$distro" == "SLES" ] || [ "$distro" == "OpenSUSE" ]; then

        # We don't need to install python on SLES due to their updated version of python
        # available with the OS itself
        if [ "$dist" == "sles15" ] || [ "$dist" == "sles12" ] || [ "$distro" == "OpenSUSE" ]; then

            zypper install gcc gcc-c++ zlib zlib-devel openssl libopenssl-devel sqlite3 sqlite3-devel libffi-devel rpm-build wget

        elif [ "$dist" == "sles11" ]; then

            # Show information about suse manual config for SDK
            echo ""
            echo "Manual configuration required:"
            echo ""
            echo "1. Register your SUSE system."
            echo "2. Install SDK repo:"
            echo "   https://www.suse.com/support/kb/doc/?id=7015337"
            if [ "$arch" == "i686" ]; then
                arch="i586";
            fi
            echo "   https://nu.novell.com/repo/\$RCE/SLE11-SDK-SP4-Pool/sle-11-$arch/rpm/$arch/sle-sdk-release-11.4-1.55.$arch.rpm"
            echo "   https://nu.novell.com/repo/\$RCE/SLE11-SDK-SP4-Pool/sle-11-$arch/rpm/$arch/sle-sdk-release-SDK-11.4-1.55.$arch.rpm"
            echo "3. Install the Security Module:"
            echo "   https://www.suse.com/documentation/suse-best-practices/singlehtml/securitymodule/securitymodule.html"
            echo ""
            echo "Press enter to continue..."
            read

            # Install base packages
            zypper install gcc gcc-c++ zlib zlib-devel sqlite3 sqlite3-devel rpm wget libffi-devel

            # Install openssl 1.0.x for TLS 1.2 support
            zypper install openssl1 libopenssl1_0_0 libopenssl1-devel libcurl4-openssl1 curl-openssl1 wget-openssl1

        fi

    elif [ "$distro" == "Raspbian" ]; then

        apt-get install gcc openssl sqlite3 libsqlite3-dev libffi-dev rpm git debian-builder alien libssl-dev -y

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

    echo "Building python..."

    # Install bundled Python version from source
    if [ $SKIP_PYTHON -eq 0 ]; then
        if [ ! -f $PYTHONTAR.tgz ]; then
            wget https://www.python.org/ftp/python/$PYTHONVERSION/$PYTHONTAR.tgz
        fi
        tar xf $PYTHONTAR.tgz
        cd $PYTHONTAR
        # Removed from configure: LDFLAGS='-Wl,-rpath,\$${ORIGIN} -Wl,-rpath,\$${ORIGIN}/lib'
        ./configure && make && make altinstall
        cd ..
        rm -rf $PYTHONTAR
        PYTHONBIN=$(which python3.9)
    fi

    # --------------------------
    #  INSTALL MODULES
    # --------------------------


    # Install modules
#     update_py_packages


    # --------------------------
    #  MISC ADDITIONS
    # --------------------------



}

set +e
useradd nagios
groupadd nagios
usermod -g nagios nagios
set -e
