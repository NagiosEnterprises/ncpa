#!/bin/bash

echo -e "***** linux/setup.sh"

# Virtual environment integration
VENV_MANAGER="$BUILD_DIR/venv_manager.sh"
export VENV_NAME="${VENV_NAME:-ncpa-build-linux}"

# Globals - defined in build.sh and version_config.sh
#     PYTHONVER, SSLVER, ZLIBVER, SKIP_PYTHON

# Skip Python detection if using virtual environment (recommended)
SKIP_PYTHON="${SKIP_PYTHON:-0}"

# Legacy Python command for fallback compatibility
PYTHONCMD="python$(echo $PYTHONVER | sed 's|\.[0-9]\{1,2\}$||g')"
echo -e "***** linux/setup.sh - PYTHONCMD (fallback): $PYTHONCMD"
echo -e "***** linux/setup.sh - SKIP_PYTHON: $SKIP_PYTHON"

set +e
if [ "$SKIP_PYTHON" -eq 0 ]; then
    PYTHONBIN=$(which $PYTHONCMD)
else
    echo -e "***** linux/setup.sh - Using virtual environment Python: $PYTHONBIN"
fi
set -e

# Get information about system
. $BUILD_DIR/linux/init.sh

# Load some installers and support functions
. $BUILD_DIR/linux/installers.sh

## Current SSL major version, e.g. 3
ssl_maj_ver=$(openssl version | egrep "[1-9].[0-9].[0-9]" | head -n1 | sed -e 's/^.*SSL \([0-9]*\)\..*/\1/')

install_prereqs() {
    echo -e "***** linux/setup.sh - install_prereqs()"
    echo -e "***** linux/setup.sh - dist: $dist"
    echo -e "***** linux/setup.sh - Installing system packages only (Python handled by venv)"

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

        # Install core system packages (no Python packages - handled by venv)
        apt-get -y update
        if [[ "$ssl_maj_ver" -lt 3 ]]; then
            echo -e "***** linux/setup.sh - apt-get install (excluding SSL, including Python build deps)"
            apt-get -y install gcc g++ rpm libffi-dev sqlite3 libsqlite3-dev wget alien \
                               python3-dev python3-venv python3-pip build-essential \
                               libbz2-dev libreadline-dev libsqlite3-dev libncurses5-dev \
                               libncursesw5-dev tk-dev libgdbm-dev libc6-dev \
                               --allow-unauthenticated
        else
            echo -e "***** linux/setup.sh - apt-get install (including SSL and Python build deps)"
            apt-get -y install gcc g++ zlib1g-dev openssl libssl-dev rpm libffi-dev sqlite3 \
                               libsqlite3-dev wget alien python3-dev python3-venv python3-pip \
                               build-essential libbz2-dev libreadline-dev libncurses5-dev \
                               libncursesw5-dev tk-dev libgdbm-dev libc6-dev \
                               --allow-unauthenticated
        fi

        # debian-builder is not nessery anymore when Debian 12 or Ubuntu24
        if [ "$dist" == "debian10" ] || [ "$dist" == "debian11" ] || [ "$dist" == "ubuntu20" ] || [ "$dist" == "ubuntu22" ]; then
            echo -e "***** linux/setup.sh - apt-get install debian-builder"
            apt-get -y update
            apt-get -y install debian-builder --allow-unauthenticated
        fi
    elif [ "$distro" == "CentOS" ] || [ "$distro" == "RHEL" ] || [ "$distro" == "Oracle" ] || [ "$distro" == "CloudLinux" ] || [ "$distro" == "Fedora" ]; then
        echo -e "***** linux/setup.sh - install_prereqs() - CentOS/RHEL"

        if [ "$distro" == "Oracle" ]; then
            if [ "$dist" == "ol8" ] || [ "$dist" == "ol9" ]; then
                dnf -y install sudo
                if [ "$dist" == "ol9" ]; then
                    dnf -y install zlib-devel openssl-devel
                fi
            fi
        fi

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
                
                # Enable CRB (CodeReady Builder) repository for development packages
                # This provides gdbm-devel and other development libraries
                if command -v dnf >/dev/null 2>&1; then
                    echo -e "***** linux/setup.sh - enabling CRB repository for development packages"
                    dnf config-manager --enable crb 2>/dev/null || true
                fi
            fi
        fi

        # Install core system packages (no Python packages - handled by venv)
        if [[ "$ssl_maj_ver" -lt 3 ]]; then
            echo -e "***** linux/setup.sh - yum install (excluding SSL, including Python build deps)"
            yum -y install gcc gcc-c++ rpm-build libffi-devel sqlite sqlite-devel wget make \
                           python3-devel python3-pip bzip2-devel readline-devel \
                           ncurses-devel gdbm-devel
        else
            echo -e "***** linux/setup.sh - yum install (including SSL and Python build deps)"
            yum -y install gcc gcc-c++ zlib zlib-devel openssl openssl-devel rpm-build \
                           libffi-devel sqlite sqlite-devel wget make python3-devel \
                           python3-pip bzip2-devel readline-devel ncurses-devel gdbm-devel
        fi

    elif [ "$distro" == "SUSE LINUX" ] || [ "$distro" == "SLES" ] || [ "$distro" == "OpenSUSE" ]; then

        # We don't need to install python on SLES due to their updated version of python
        # available with the OS itself
        if [ "$dist" == "sles15" ] || [ "$dist" == "sles12" ] || [ "$distro" == "OpenSUSE" ]; then

        if [[ "$ssl_maj_ver" -lt 3 ]]; then
            echo -e "***** linux/setup.sh - zypper install (excluding SSL, including Python build deps)"
            zypper -n update
            zypper -n install gcc gcc-c++ sqlite3 sqlite3-devel libffi-devel rpm-build wget \
                              python3-devel python3-pip libbz2-devel readline-devel \
                              ncurses-devel gdbm-devel
        else
            echo -e "***** linux/setup.sh - zypper install (including SSL and Python build deps)"
            zypper -n update
            zypper -n install gcc gcc-c++ zlib zlib-devel openssl libopenssl-devel sqlite3 \
                              sqlite3-devel libffi-devel rpm-build wget python3-devel \
                              python3-pip libbz2-devel readline-devel ncurses-devel gdbm-devel
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
            zypper -n install gcc gcc-c++ zlib zlib-devel sqlite3 sqlite3-devel rpm wget libffi-devel

            # Install openssl 1.0.x for TLS 1.2 support
            zypper -n install openssl1 libopenssl1_0_0 libopenssl1-devel libcurl4-openssl1 curl-openssl1 wget-openssl1

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

    # Skip Python installation and package management - handled by virtual environment
    if [ "$SKIP_PYTHON" -eq 1 ]; then
        echo -e "***** linux/setup.sh - Skipping Python/package installation - handled by virtual environment"
    else
        echo -e "***** linux/setup.sh - WARNING: Fallback mode - installing Python from source"
        # -----------------------------------------
        #  INSTALL SYSTEM REQS - BUILD FROM SOURCE
        # -----------------------------------------

        # Install Python version from source (fallback mode)
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

        # Install modules (fallback mode)
        update_py_packages
    fi
}

# This must be outside of install_prereqs(), so it will be executed during workflow build.

echo -e "***** linux/setup.sh - add users/groups"
set +e
useradd -s /sbin/nologin nagios 
groupadd nagios
usermod -g nagios nagios
set -e

# Automatically install Python requirements in venv after setup
if [ -n "$VENV_MANAGER" ] && [ -x "$VENV_MANAGER" ]; then
    "$VENV_MANAGER" install-requirements
fi
