function valid_python_version()
{
    if [ `python -c 'import sys; assert sys.version_info >= (2, 6)' 2>&1` ];
    then
        echo Python version is not correct. Python 2.6 or greater is required.
        return 1
    fi
}

function binary_installed()
{
    for binary in $@
    do
        if [ ! `which $binary 2> /dev/null` ];
        then
            echo "$binary not installed. This must be installed."
            return 1
        fi
    done
}
