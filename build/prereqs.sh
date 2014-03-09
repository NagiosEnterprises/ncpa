#!/bin/bash

set -e

if ! which gcc > /dev/null;
then
    echo 'gcc must be installed to continue.'
    exit 1
elif ! which wget > /dev/null;
then
    echo 'wget must be installed to continue.'
    exit 1
elif ! which make > /dev/null;
    echo 'make must be installed to continue.'
    exit 1
fi

# Build a Python for the system, regardless of whether or not it exists
cd /tmp
wget 'http://www.python.org/ftp/python/2.7.6/Python-2.7.6.tgz'
tar xf Python-2.7.6.tgz
cd Python-2.7.6
./configure
make
make altinstall
cd ..
rm -rf Python-2.7.6*

# Install pip
wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
python2.7 get-pip.py
rm -f get-pip.py

# Install cx_Freeze
wget 'http://downloads.sourceforge.net/project/cx-freeze/4.3.2/cx_Freeze-4.3.2.tar.gz?r=http%3A%2F%2Fcx-freeze.sourceforge.net%2F&ts=1394344052&use_mirror=iweb' -O cx_Freeze-4.3.2.tar.gz
tar xf cx_Freeze-4.3.2.tar.gz
cd cx_Freeze-4.3.2
python2.7 setup.py install
cd ..
rm -rf cx_Freeze*
