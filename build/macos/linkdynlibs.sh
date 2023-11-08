#!/usr/bin/env bash

# Convert relative paths to absolute paths, for python's .so dylib dependencies.
# E.g. '@loader_path/../../ ... /../opt/xyz.dylib' to '/usr/local/opt/xyz.dylib',
# so they can be copied to the cx_freeze directory.
dylibname=""
badpath=""
soname=""

# Example path values
# dynlibpath="/usr/local/Cellar/python@3.11/3.11.4_1/Frameworks/Python.framework/Versions/3.11/lib/python3.11/lib-dynload"
# gdpath="/usr/local/opt"
# badpath="@loader_path/../../../../../../../../../../opt"
# soname="_sqlite3.cpython-311-darwin.so"
# dylibname="sqlite/lib/libsqlite3.0.dylib"

# Calculate real paths
# !!! YOU MUST RUN setPaths BEFORE ANY OTHER COMMANDS !!!
# Must be run after python install to set up default paths
setPaths() {
    if [[ ! -z $1 ]]; then
        dynlibpath=$1
    else
        if [[ -z $PYTHONVER ]]; then
            PYTHONVER="3.11.3"
        fi
        python_at_seg=python@$(echo $PYTHONVER | sed 's|\.[0-9]\{1,2\}$||g')

        if [[ -z $HOMEBREW_CELLAR ]]; then
            eval "$(brew shellenv)"
        fi
        dynlibpath=$(find $HOMEBREW_CELLAR/$python_at_seg -name *.so | grep "lib-dynload" | head -n1 | sed 's~/lib-dynload/.*~/lib-dynload~g')
        echo "dynlibpath: $dynlibpath"
    fi

    if [[ ! -z $2 ]]; then
        badpath=$2
    else
        badpath=$(otool -L $dynlibpath/* | grep "\.\./" | head -n1 | sed -e 's~opt/.*~opt~g' | sed 's/\t//g')
        echo "badpath: $badpath"
    fi

    if [[ ! -z $3 ]]; then
        gdpath=$3
    else
        gdpath="$HOMEBREW_PREFIX/opt"
        echo "gdpath: $gdpath"
    fi
}

setupOK() {
    if [[ ! -z $dynlibpath ]] && [[ ! -z $badpath ]] && [[ ! -z $gdpath ]]; then
        return 0
    else
        echo "ERROR: You must run 'setPaths' before any other functions"
        return 1
    fi
}
# Utility to show specific lib dependencies or all lib dependencies
showLib() {
    if setupOK; then
        f=$1
        if [[ -z $1 ]]; then
            otool -L $dynlibpath/*
        else
            otool -L $dynlibpath/$f
        fi
    fi
}

# List libs and dependencies where some dependencies have relative paths
# Filter any previously fixed dependencies so this can be used iteratively
# for libs with multiple relative dependencies.
listBadLibs() {
    if setupOK; then
        otool -L $dynlibpath/* | grep -v "$gdpath" | grep -B1 "$badpath"
    fi
}

# Find the python dynamic libraries with relative paths, and convert them to
# a string consumable as an array of tilda delimited so:dylib pairs.
# E.g., _ssl.cpython-311-darwin.so~openssl@3/lib/libcrypto.3.dylib
getBadLibs() {
    if setupOK; then
        # Get otool listing of libs with dependencies with relative paths
        # Strip everything but .so and .dylib names
        badlibs=$(listBadLibs | sed -e 's~(compat.*)~~g' | sed -e "s~:~~g" | sed -e 's~/\.\.~~g' | sed -e 's~\t@loader_path/opt/~~' | sed -e 's~/.*/_~_~g' | sed -e 's~:~~g')

        # Format so that list can be consumed as an array of tilda delimited pairs
        badlibs=$(echo $badlibs | sed -e 's/ -- /|/g' | sed -e 's/ /~/g' | sed -e 's/|/ /'g)
        echo $badlibs
    fi
}

# Uses install_name_tool to fix a dependency in a library
# by replacing the dependency's relative path with an absolute path.
# Requires two params: lib name, dependency lib name
fixLib() {
    if setupOK; then
        if [[ ! -z $1 ]]; then
            soname=$1
            if [[ ! -z $2 ]]; then
                dylibname=$2
            else
                echo "Please provide a .dylib file name, e.g. 'sqlite/lib/libsqlite3.0.dylib'"
                return
            fi
        else
            echo "Please provide and .so file name, e.g. '_sqlite3.cpython-311-darwin.so'"
            return
        fi

        echo "Fixing $soname"
        echo "    Changing: $badpath/$dylibname"
        echo "    To:       $gdpath/$dylibname"

        sudo install_name_tool -change "$badpath/$dylibname" "$gdpath/$dylibname" "$dynlibpath/$soname"
    fi
}

fixLibs() {
    if setupOK; then
        echo "Fixing libs in $dynlibpath..."
        badlibs=$(getBadLibs)

        while [ "$badlibs" != "" ]
        do
#             echo "badlibs: $badlibs"
            badlibs=($badlibs)

            for badlib in "${badlibs[@]}"
            do
                echo -e "\n----------------"
#                 echo "badlib: $badlib"
                solibname=$(echo ${badlib} | cut -f1 -d~)
                dynlibname=$(echo ${badlib} | cut -f2 -d~)
#                 echo -e "    so: $solibname\n    dylib: $dynlibname"
                fixLib $solibname $dynlibname
            done
            badlibs=$(getBadLibs)
        done
    fi
}
