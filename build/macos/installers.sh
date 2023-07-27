#!/usr/bin/env bash

# Scripts to install homebrew, OpenSSL and Python, and update python libraries

# Utility scripts
has_openssl() {
    local installchk=$(openssl version | grep $1)
    echo $installchk
}

has_python() {
    local installchk=$($PYTHONCMD -c "import sys; print(sys.version)" | grep $1)
    echo $installchk
}

# Installs tools needed to make and install OpenSSL, zLib, and Python
install_devtools() {
    echo -e "\nInstalling xcode commmand line tools..."
    xcode-select --install

    if [ -z $( which brew 2>/dev/null ) ]; then
        echo -e "Installing Homebrew package manager..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    BREWBIN="/usr/local/bin/brew"

    # Add brew env vars to your environment
    (echo; echo 'eval "$($BREWBIN shellenv)"') >> ~/.bash_profile
    eval "$($BREWBIN shellenv)"

    echo -e "Installing misc brew packages: pkg-config xz gdbm ..."
    $BREWBIN update
    $BREWBIN install pkg-config xz gdbm
}

install_openssl() {
    local ssl_new_version=""

    if [[ ! -z $1 ]]; then
        ssl_new_version=$1
    else
        echo -e "ERROR! install_openssl() - No OpenSSL version provided!"
        echo -e "********************************************\n\n"
        return 1
    fi

    # Make version shorter for homebrew, e.g. 3.1
    ssl_new_version=$(echo $ssl_new_version | sed 's|\.[0-9]\{1,2\}$||g')

    echo -e "\n\n********************************************"
    echo -e "Installing OpenSSL $ssl_new_version..."
    echo -e " "

    $BREWBIN install openssl@$ssl_new_version

    # Install additional dev tools requiring openssl (Do I need this?)
    $BREWBIN install tcl-tk

    local installchk=$(has_openssl $ssl_new_version)
    echo -e "\installchk: $installchk"
    echo -e "\n\n********************************************"

    if [[ ! -z $installchk ]]; then
        echo -e "SUCCESS! OpenSSL $ssl_new_version is installed"
        echo -e "********************************************\n\n"
        return 0
    else
        echo -e "ERROR! OpenSSL $ssl_new_version failed to install correctly"
        echo -e "********************************************\n\n"
        return 1
    fi
}

install_python() {
    local python_new_version=""

    if [[ ! -z $1 ]]; then
        python_new_version=$1
    else
        if [[ ! -z $PYTHONVER ]]; then
            python_new_version=$PYTHONVER
        else
            echo -e "ERROR! install_python() - No Python version provided!"
            echo -e "********************************************\n\n"
            return 1
        fi
    fi

    # Make version shorter for homebrew, e.g. 3.11
    python_new_version=$(echo $python_new_version | sed 's|\.[0-9]\{1,2\}$||g')

    echo -e "\n\n********************************************"
    echo -e "Installing Python $python_new_version...\n"

    $BREWBIN install python@$python_new_version

    local installchk=$(has_python $python_new_version)
    echo -e "\installchk: $installchk"
    echo -e "\n\n********************************************"

    if [[ ! -z $installchk ]]; then
        echo -e "SUCCESS! Python $ssl_new_version is installed"
        echo -e "********************************************\n\n"
        return 0
    else
        echo -e "ERROR! Python $ssl_new_version failed to install correctly"
        echo -e "********************************************\n\n"
        return 1
    fi
}

# Requires globals $PYTHONBIN, $PYTHONVER, $PYTHONCMD and $BUILD_DIR
update_py_packages() {
    echo -e "\n***** macos/installers.sh - update_py_packages()"
    $PYTHONBIN -m pip install --upgrade pip
    $PYTHONBIN -m pip install -r $BUILD_DIR/resources/require.txt --upgrade

    # cx freeze doesn't grab the proper _sslxxx.so and other dynamic libs, so we copy in the real ones.
    echo -e "    cx_freeze doesn't grab the proper _sslxxx.so and other dynamic libs, so we copy in the real ones..."

    python_at_seg=python@$(echo $PYTHONVER | sed 's|\.[0-9]\{1,2\}$||g')

    cxlibpath="/usr/local/lib/$PYTHONCMD/site-packages/cx_Freeze/bases"
    echo "cxlibpath: $cxlibpath"
    pylibpath=$(find $HOMEBREW_CELLAR/$python_at_seg -name *.so | grep "lib-dynload" | head -n1 | sed 's~/lib-dynload/.*~~g')
    echo "pylibpath: $pylibpath"

    echo -e "***** macos/installers.sh - update_py_packages() - copy $pylibpath/lib-dynload to cx_freeze lib-dynload"

    if [ ! -d "$cxlibpath/lib-dynload_orig" ]; then
        mkdir $cxlibpath/lib-dynload_orig
    fi
    cp $cxlibpath/lib-dynload/* $cxlibpath/lib-dynload_orig/

    # Link python's lib-dynload to cx_freeze lib-dynload to make sure we are using desired OpenSSL, etc.
    cp $pylibpath/lib-dynload/* $cxlibpath/lib-dynload/
}
