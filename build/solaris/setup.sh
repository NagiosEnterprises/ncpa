#!/bin/bash

# Globals
PYTHONVER="3.9.13"
PYTHONTAR="Python-$PYTHONVER"
PYTHONBIN=$(which python3)

# Check version of Solaris
SOLARIS=11
ARCH="x86"

update_py_packages() {
    # Do special things for Solaris 11 (do not build with special flags)
    if [ $SOLARIS -eq 11 ]; then
        $PYTHONBIN -m pip install --upgrade pip
        $PYTHONBIN -m pip install -r $BUILD_DIR/resources/require.txt --upgrade
    else
        echo "Cannot built on Solaris 10. Not a supported OS."
        exit 1
    fi
}

install_prereqs() {


    # --------------------------
    #  INSTALL SYSTEM REQS
    # --------------------------


    # Install pre-reqs for Solaris systems
    if [ ! -f /usr/bin/gcc ]; then
        pkg install --accept gcc libffi zlib
    fi


    # --------------------------
    #  
    # --------------------------


    cd $BUILD_DIR/resources

    pkgadd -d http://get.opencsw.org/now
    /opt/csw/bin/pkgutil -U
    /opt/csw/bin/pkgutil -y -i python33
    rm -rf $PYTHONTAR

    # Install pip python modules
    update_py_packages


    # --------------------------
    #  MISC ADDITIONS
    # --------------------------


    useradd nagios
    groupadd nagios
    usermod -g nagios nagios


}
