#!/usr/bin/env bash

# Scripts to install homebrew, OpenSSL and Python, and update python libraries

# Load utilities to fix dynamic libs
. $BUILD_DIR/macos/linkdynlibs.sh
os_version=$(sw_vers -productVersion)
os_major_version=$(echo $os_version | cut -f1 -d.)
os_minor_version=$(echo $os_version | cut -f2 -d.)

# Utility scripts

has_python() {
    local installchk=$($PYTHONCMD -c "import sys; print(sys.version)" | grep $1)
    echo $installchk
}

# Installs tools needed to make and install OpenSSL, zLib, and Python
install_devtools() {
    echo -e "\n***** macos/installers.sh - install_devtools()"
    echo -e "    - Installing Homebrew and dev tools on MacOS $os_version..."

    if [[ -z $(xcode-select --version 2>/dev/null) ]]; then
        echo -e "\n    - Installing xcode commmand line tools..."
        xcode-select --install
    else
        echo -e "\n    - Xcode commmand line tools already installed"
    fi

    BREWBIN="/usr/local/bin/brew"
    if [ -z $( which brew 2>/dev/null ) ]; then
        echo -e "    - Installing Homebrew package manager..."
        if [[ "$os_major_version" == "10" ]]; then
            export HOMEBREW_NO_INSTALL_FROM_API=1
        fi
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    else
        echo -e "\n    - Homebrew already installed"
    fi

    # Add brew env vars to your environment
    echo -e "\n$(eval "$($BREWBIN shellenv)")" | sudo tee -a ~/.bash_profile > /dev/null
    eval "$($BREWBIN shellenv)"

    echo -e "    - Installing misc brew packages: pkg-config xz gdbm..."
    $BREWBIN update
    $BREWBIN install pkg-config xz gdbm
    if [[ "$os_major_version" == "10" ]]; then
        echo -e "    - Installing libffi (MacOS v10.x only)..."
        $BREWBIN install libffi
    fi

}

install_python() {
    echo -e "\n***** macos/installers.sh - install_python()"
    # Note Python 3.11+ requires OpenSSL 3+ as a dependency, so there is no need to install it separately.
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
    echo -e "Installing Python $python_new_version with OpenSSL...\n"

    $BREWBIN install python@$python_new_version

    local installchk=$(has_python $python_new_version)
    echo -e "\installchk: $installchk"
    echo -e "\n\n********************************************"

    if [[ ! -z $installchk ]]; then
        echo -e "SUCCESS! Python $python_new_version is installed"
        echo -e "********************************************\n\n"
        return 0
    else
        echo -e "ERROR! Python $python_new_version failed to install correctly"
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
    echo "    cxlibpath: $cxlibpath"

    eval "$($BREWBIN shellenv)"

    pylibpath=$(find $HOMEBREW_CELLAR/$python_at_seg -name *.so | grep "lib-dynload" | head -n1 | sed 's~/lib-dynload/.*~~g')
    echo "    pylibpath: $pylibpath"

    echo -e "    - copy $pylibpath/lib-dynload to cx_freeze lib-dynload"

    # For MacOS 11+ libraries need special treatment
    if [[ "$os_major_version" != "10" ]]; then
        if [ ! -d "$pylibpath/lib-dynload_orig" ]; then
            sudo mkdir $pylibpath/lib-dynload_orig
            sudo cp $pylibpath/lib-dynload/* $pylibpath/lib-dynload_orig/
        fi
        # Define paths for dependency link fixer
        setPaths

        #Convert relative dependency paths to absolute
        fixLibs
    fi

    if [ ! -d "$cxlibpath/lib-dynload_orig" ]; then
        sudo mkdir $cxlibpath/lib-dynload_orig
        sudo cp $cxlibpath/lib-dynload/* $cxlibpath/lib-dynload_orig/
    fi


    # Link python's lib-dynload to cx_freeze lib-dynload to make sure we are using desired OpenSSL, etc.
    sudo cp $pylibpath/lib-dynload/* $cxlibpath/lib-dynload/
}
