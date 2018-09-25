#!/bin/bash

# Globals
PYTHONTAR="Python-2.7.14"
PYTHONVER="python2.7"
PYTHONBIN="/usr/local/bin/python2.7"
CXFREEZEVER="cx_Freeze-4.3.4"

install_prereqs() {

    # --------------------------
    #  INSTALL SYSTEM REQS
    # --------------------------


    # Install pre-reqs for Solaris systems
    pkg install gcc libffi zlib


    # --------------------------
    #  INSTALL SOURCE FILES
    # --------------------------


    cd $DIR/../resources

    # Install bundled Python version from source if needed
    tar xf $PYTHONTAR.tgz
    cd $PYTHONTAR && ./configure --with-zlib=/usr/include --enable-shared && make && make altinstall
    cd ..

    # Install the patched version of cx_Freeze
    tar xf $CXFREEZEVER.tar.gz
    cd $CXFREEZEVER
    $PYTHONBIN setup.py install
    cd ..

    # Clean up resource directory
    rm -rf $PYTHONTAR
    rm -rf $CXFREEZEVER


    # --------------------------
    #  INSTALL PIP & PIP MODULES
    # --------------------------


    # Install pip
    cd /tmp && wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py && $PYTHONBIN /tmp/get-pip.py

    # Install pip python modules
    CFLAGS="-I/usr/lib/amd64/libffi-3.2.1/include" $PYTHONBIN -m pip install -r $BASEDIR/../resources/require.txt --upgrade


    # --------------------------
    #  MISC ADDITIONS
    # --------------------------


    useradd nagios
    groupadd nagios
    usermod -g nagios nagios

}
