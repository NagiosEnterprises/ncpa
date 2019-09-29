#!/bin/bash -e

# Gets OS information - Essentially a frontend for lsb_release but with
# extra logic for RHEL-based and SuSE-based systems, because minimal RHEL installations
# don't have lsb_release by default and SuSE doesn't have it either. Also added support
# for Unix systems like Mac OS X.

unixtype=`uname -s`

# Make sure we're on a Linux distro
if [ $unixtype != "Linux" ] && [ $unixtype != "Darwin" ]; then
    echo "ERROR: Unsupported OS detected. This script only detects Linux / Mac OS X distributions." >&2
    exit 2
fi

# Get architecture
architecture=`uname -m`

# Get OS & version
if [ $unixtype == "Linux" ]; then
    if [ -r /etc/redhat-release ]; then
        if rpm -q centos-release; then
            distro="CentOS"
        elif rpm -q sl-release; then
            distro="Scientific"
        elif [ -r /etc/oracle-release ]; then
            distro="Oracle"
        elif rpm -q cloudlinux-release; then
            distro="CloudLinux"
        elif rpm -q fedora-release; then
            distro="Fedora"
        elif rpm -q redhat-release || rpm -q redhat-release-server; then
            distro="RHEL"
        fi >/dev/null
        version=`sed 's/.*release \([0-9.]\+\).*/\1/' /etc/redhat-release`
    elif [ -r /etc/os-release ]; then
        source /etc/os-release
        if [ -n "$NAME" ]; then
            distro=$NAME
            version=$VERSION_ID
        fi
    elif which lsb_release &>/dev/null; then
        distro=`lsb_release -si`
        version=`lsb_release -sr`
    fi
elif [ $unixtype == "Darwin" ]; then
    distro="MacOSX"
    version=`sw_vers -productVersion`
fi

# Verify Debian system versions
if [ "$distro" == "Debian GNU/Linux" ]; then
    distro="Debian"
fi

# Verify Raspbian system versions
if [ "$distro" == "Raspbian GNU/Linux" ]; then
    distro="Raspbian"
fi

# Add patch level to the version of SLES (because they don't...)
if [ "$distro" == "openSUSE Tumbleweed" ] || [ "$distro" == "openSUSE Leap" ] || [ "$distro" == "openSUSE" ]; then
    distro="OpenSUSE"
fi

# Verify that we have a distro now
if [ -z "$distro" ]; then
    echo "ERROR: Could not determine OS. Please make sure lsb_release is installed or your OS info is in /etc/os-release." >&2
    exit 1
fi

# OS-related variables have a detailed long variable, and a more useful short
# one: distro/dist, version/ver, architecture/arch. If in doubt, use the short
# short major version, e.g. "6" instead of "6.2"
ver="${version%%.*}"

# Set dist variable like before (el5/el6 on both CentOS & Red Hat)
case "$distro" in
    "CentOS" | "RHEL" | "Oracle" | "CloudLinux" )
        dist="el$ver"
        ;;
    "Fedora" )
        dist="fedora$ver"
        ;;
    "Debian" )
        dist="debian$ver"
        ;;
    "Raspbian" )
        dist="rasp$ver"
        ;;
    "OpenSUSE" )
        dist="os$ver"
        ;;
    "MacOSX" )
        dist="osx$ver"
        ;;
    "SLES" )
        dist="sles$ver"
        ;;
    *)
        dist=$(echo "$distro$ver" | tr A-Z a-z)
esac

# The i386 is a more useful value than i686 for el5, because repo paths and
# package names typically use i386
if [ "$dist $architecture" = "el5 i686" ]; then
    arch="i386"
else
    arch="$architecture"
fi
