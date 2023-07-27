#!/bin/bash

echo -e "***** linux/setup.sh"

# Globals - defined in build.sh
#     PYTHONVER, SSLVER, ZLIBVER

# Make python command, e.g. python3.11
PYTHONCMD="python$(echo $PYTHONVER | sed 's|\.[0-9]\{1,2\}$||g')"
echo -e "***** linux/setup.sh - PYTHONCMD: $PYTHONCMD"

set +e
PYTHONBIN=$(which $PYTHONCMD)
set -e
SKIP_PYTHON=0

# Get information about system
. $BUILD_DIR/linux/init.sh

# Load some installers and support functions
. $BUILD_DIR/linux/installers.sh

## Current SSL major version, e.g. 3
ssl_maj_ver=$(openssl version | egrep "[1-9].[0-9].[0-9]" | head -n1 | sed -e 's/^.*SSL \([0-9]*\)\..*/\1/')

install_prereqs() {
    echo -e "***** linux/setup.sh - install_prereqs()"
    echo -e "***** linux/setup.sh - dist: $dist"

    # --------------------------
    #  INSTALL SYSTEM REQS - PACKAGES
    # --------------------------

    if [ "$distro" == "Debian" ] || [ "$distro" == "Ubuntu" ]; then
        echo -e "***** linux/setup.sh - install_prereqs() - Debian/Ubuntu"

        # deb9 apt sources are no longer valid. This is solved by deb8 installer, but not deb9.
        if [[ "$dist" == "debian9" ]]; then
            mv /etc/apt/sources.list /etc/apt/sources.list.orig
            echo "deb http://archive.debian.org/debian/ stretch  main contrib non-free" >> /etc/apt/sources.list
            echo "deb http://security.debian.org/ stretch/updates main contrib non-free" >> /etc/apt/sources.list
            cat /etc/apt/sources.list
        fi

        # If we are going to build and install SSL from source, no need to install it here
        if [[ "$ssl_maj_ver" -lt 3 ]]; then
            echo -e "***** linux/setup.sh - apt-get install with excluding SSL pkgs"
            apt-get -y update
            apt-get -y install gcc g++ debian-builder rpm libffi-dev sqlite3 libsqlite3-dev wget alien  --allow-unauthenticated
        else
            echo -e "***** linux/setup.sh - apt-get install with SSL pkgs"
            apt-get -y update
            apt-get -y install gcc g++ zlib1g-dev openssl libssl-dev debian-builder rpm libffi-dev sqlite3 libsqlite3-dev wget alien  --allow-unauthenticated
        fi

    elif [ "$distro" == "CentOS" ] || [ "$distro" == "RHEL" ] || [ "$distro" == "Oracle" ] || [ "$distro" == "CloudLinux" ]; then
        echo -e "***** linux/setup.sh - install_prereqs() - CentOS/RHEL"

        if [ "$dist" == "el7" ]; then
            if [ -f /etc/yum.repos.d/epel.repo ]; then
                echo -e "***** linux/setup.sh - fix yum.repos.d"
                # epel repo metalinks aren't valid for early distros, so we use baseurls instead.
                sed -i -e s/^#baseurl/baseurl/g -e s/^metalink/#metalink/g /etc/yum.repos.d/epel*
            fi

            yum -y install epel-release
            if [ -f /etc/yum.repos.d/epel.repo ]; then
                sed -i -e s/^#baseurl/baseurl/g -e s/^metalink/#metalink/g /etc/yum.repos.d/epel*
            fi
        else
            if [ "$distro" == "CentOS" ]; then
                yum -y install epel-release
            fi
        fi

        # If we are going to build and install SSL from source, no need to install it here
        if [[ "$ssl_maj_ver" -lt 3 ]]; then
            echo -e "***** linux/setup.sh - yum install excluding SSL pkgs"
            yum -y install gcc gcc-c++ rpm-build libffi-devel sqlite sqlite-devel wget make
        else
            echo -e "***** linux/setup.sh - yum install with SSL pkgs"
            yum -y install gcc gcc-c++ zlib zlib-devel openssl openssl-devel rpm-build libffi-devel sqlite sqlite-devel wget make
        fi

    elif [ "$distro" == "SUSE LINUX" ] || [ "$distro" == "SLES" ] || [ "$distro" == "OpenSUSE" ]; then

        # We don't need to install python on SLES due to their updated version of python
        # available with the OS itself
        if [ "$dist" == "sles15" ] || [ "$dist" == "sles12" ] || [ "$distro" == "OpenSUSE" ]; then

        if [[ "$ssl_maj_ver" -lt 3 ]]; then
            echo -e "***** linux/setup.sh - apt-get install with excluding SSL pkgs"
            zypper -n update
            zypper -n install gcc gcc-c++ sqlite3 sqlite3-devel libffi-devel rpm-build wget
        else
            echo -e "***** linux/setup.sh - apt-get install with SSL pkgs"
            zypper -n update
            zypper -n install gcc gcc-c++ zlib zlib-devel openssl libopenssl-devel sqlite3 sqlite3-devel libffi-devel rpm-build wget
        fi

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


    # -----------------------------------------
    #  INSTALL SYSTEM REQS - BUILD FROM SOURCE
    # -----------------------------------------

    # Install Python version from source
    if [ $SKIP_PYTHON -eq 0 ]; then

        # First update OpenSSL if necessary
        if [[ "$ssl_maj_ver" -lt 3 ]]; then
            cd $BUILD_DIR/resources
            install_ssl_and_zlib $SSLVER $ZLIBVER
        else
            echo -e "***** linux/setup.sh - OpenSSL version already greater than 3. Not changed."
        fi

        echo -e "***** linux/setup.sh - Building python..."
        cd $BUILD_DIR/resources
        install_python $PYTHONVER
        PYTHONBIN=$(which $PYTHONCMD)
        echo -e "***** linux/setup.sh - after Py install PYTHONBIN: $PYTHONBIN"
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
useradd nagios
groupadd nagios
usermod -g nagios nagios
set -e
