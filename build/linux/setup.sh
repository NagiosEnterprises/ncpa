#!/bin/bash

echo -e "***** linux/setup.sh"

# Globals
PYTHONVER="3.11.3"
PYTHONCMD="python3.11"
PYTHONTAR="Python-$PYTHONVER"
set +e
PYTHONBIN=$(which $PYTHONCMD)
set -e
SKIP_PYTHON=0

# Get information about system
. $BUILD_DIR/linux/init.sh

update_py_packages() {
    echo -e "***** linux/setup.sh - update_py_packages()"
    $PYTHONBIN -m pip install --upgrade pip
    # LDFLAGS='-Wl,-rpath,\${ORIGIN} -Wl,-rpath,\${ORIGIN}/lib' $PYTHONBIN -m pip install -r $BUILD_DIR/resources/require.txt --upgrade --no-binary :all:
    $PYTHONBIN -m pip install -r $BUILD_DIR/resources/require.txt --upgrade
}

install_prereqs() {
    echo -e "***** linux/setup.sh - install_prereqs()"
    echo -e "***** linux/setup.sh - dist: $dist"

    # SSL version as an integer, e.g. 101
    ssl_ver=$(openssl version | grep -e "[1-3].[0-9].[0-9]" -o | head -n1 | sed 's/\.//g')
    echo -e "***** linux/setup.sh - ssl_ver: $ssl_ver"


    # --------------------------
    #  INSTALL SYSTEM REQS
    # --------------------------


    if [ "$distro" == "Debian" ] || [ "$distro" == "Ubuntu" ]; then
        echo -e "***** linux/setup.sh - install_prereqs() - Debian/Ubuntu"
        echo -e "***** linux/setup.sh - PYTHONTAR: $PYTHONTAR"

        # If openssl is 2.0.0 or greater, it may have been manually installed, so don't try and install a new package
        if (( "$ssl_ver" >= 200 )); then
            echo -e "***** linux/setup.sh - apt-get install NO SSL"
            apt-get install gcc g++ debian-builder rpm libffi-dev sqlite3 libsqlite3-dev wget alien -y
        else
            echo -e "***** linux/setup.sh - apt-get install with SSL"
            apt-get install gcc g++ zlib1g-dev openssl libssl-dev debian-builder rpm libffi-dev sqlite3 libsqlite3-dev wget alien -y
        fi

    elif [ "$distro" == "CentOS" ] || [ "$distro" == "RHEL" ] || [ "$distro" == "Oracle" ] || [ "$distro" == "CloudLinux" ]; then
        echo -e "***** linux/setup.sh - install_prereqs() - CentOS/RHEL"

        if [ "$dist" == "el7" ]; then
            if [ -f /etc/yum.repos.d/epel.repo ]; then
                echo -e "***** linux/setup.sh - fix yum.repos.d"
                # epel repo metalinks aren't valid for early distros, so we use baseurls instead.
                sed -i -e s/^#baseurl/baseurl/g -e s/^metalink/#metalink/g /etc/yum.repos.d/epel*
            fi

            yum install epel-release -y
            if [ -f /etc/yum.repos.d/epel.repo ]; then
                sed -i -e s/^#baseurl/baseurl/g -e s/^metalink/#metalink/g /etc/yum.repos.d/epel*
            fi
        else
            yum install epel-release -y
        fi

        # If openssl is 2.0.0 or greater, it may have been manually installed, so don't try and install a new package
        if (( "$ssl_ver" >= 200 )); then
            echo -e "***** linux/setup.sh - yum install NO SSL"
            yum install gcc gcc-c++ rpm-build libffi-devel sqlite sqlite-devel wget make -y
        else
            echo -e "***** linux/setup.sh - yum install with SSL"
            yum install gcc gcc-c++ zlib zlib-devel openssl openssl-devel rpm-build libffi-devel sqlite sqlite-devel wget make -y
        fi

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

    # Install bundled Python version from source
    if [ $SKIP_PYTHON -eq 0 ]; then
        echo -e "***** linux/setup.sh - Building python..."

        if [ ! -f $PYTHONTAR.tgz ]; then
            wget https://www.python.org/ftp/python/$PYTHONVER/$PYTHONTAR.tgz
        fi
        tar xf $PYTHONTAR.tgz
        cd $PYTHONTAR
        # Removed from configure: LDFLAGS='-Wl,-rpath,\$${ORIGIN} -Wl,-rpath,\$${ORIGIN}/lib'
        # ./configure LDFLAGS='-Wl,-rpath,\$${ORIGIN} -Wl,-rpath,\$${ORIGIN}/lib' && make && make altinstall
    	./configure && make && make altinstall
        cd ..
        rm -rf $PYTHONTAR
        PYTHONBIN=$(which $PYTHONCMD)
        export PATH=$PATH:$BUILD_DIR/bin
    fi

    # --------------------------
    #  INSTALL MODULES
    # --------------------------


    # Install modules
    update_py_packages


    # --------------------------
    #  MISC ADDITIONS
    # --------------------------

}

# This must be outside of install_prereqs(), so it will be executed during workflow build.
echo -e "***** linux/setup.sh - add users/groups"
set +e
sudo useradd nagios
sudo groupadd nagios
sudo usermod -g nagios nagios
set -e
