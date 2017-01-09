#!/bin/bash
#
# Linux Build Server Setup Script
# Creates a functioning build environment on a linux server
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHONTAR="Python-3.5.2"
PYTHONVER="python3.5"
PYTHONBIN="/usr/local/bin/python3.5"

# --------------------------
#  INSTALL PRE-REQS
# --------------------------
./linux_build_prereqs.sh

# --------------------------
#  INSTALL RESOURCES
# --------------------------

cd $DIR/../resources

# Install Python
tar xf $PYTHONTAR.tgz
cd $PYTHONTAR && ./configure --with-zlib=/usr/include --enable-shared && make && make altinstall
echo '/usr/local/lib' >> /etc/ld.so.conf 
/sbin/ldconfig

# Clean up resource directory
cd ..
rm -rf $PYTHONTAR

# --------------------------
#  INSTALL PIP
# --------------------------

cd /tmp && wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py && $PYTHONBIN /tmp/get-pip.py

# --------------------------
#  INSTALL PIP COMPONENTS
# --------------------------

$DIR/update_python_packages.sh

# --------------------------
#  MISC SETUP
# --------------------------

# Add users if they don't exist
useradd nagios
groupadd nagios
