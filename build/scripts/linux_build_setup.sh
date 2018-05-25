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
if [ "$BUILDFROM" != "travis" ]; then
	./linux_build_prereqs.sh
fi

# --------------------------
#  INSTALL RESOURCES
# --------------------------

cd $DIR/../resources

# Install bundled Python version from source if needed
if [ "$BUILDFROM" != "travis" ]; then
	tar xf $PYTHONTAR.tgz
	cd $PYTHONTAR && ./configure --with-zlib=/usr/include --enable-shared && make && make altinstall
	echo '/usr/local/lib' >> /etc/ld.so.conf 
	/sbin/ldconfig
	cd ..
else
	PYTHONVER="python"
	PYTHONBIN="python"
fi

# Clean up resource directory
rm -rf $PYTHONTAR

# --------------------------
#  INSTALL PIP
# --------------------------

if [ "$BUILDFROM" != "travis" ]; then
	cd /tmp && wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py && $PYTHONBIN /tmp/get-pip.py
fi

# --------------------------
#  INSTALL PIP COMPONENTS
# --------------------------

$DIR/update_python_packages.sh

# --------------------------
#  MISC SETUP
# --------------------------

# Add users if they don't exist
if [ "$BUILDFROM" != "travis" ]; then
	useradd nagios
	groupadd nagios
	usermod -g nagios nagios
else
	sudo useradd nagios
	sudo groupadd nagios
	sudo usermod -g nagios nagios
fi