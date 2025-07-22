#!/bin/bash

echo "=== Solaris 11 IPS Package Search for Common Libraries ==="
echo ""

if ! command -v pkg >/dev/null 2>&1; then
    echo "ERROR: IPS package manager not available"
    echo "This script requires Solaris 11 or later with IPS"
    exit 1
fi

echo "System Information:"
echo "  OS: $(uname -sr)"
echo "  IPS Publisher: $(pkg publisher | head -1)"
echo ""

echo "Current Python Installations:"
for py_path in /usr/bin/python* /opt/csw/bin/python* /usr/local/bin/python*; do
    if [ -x "$py_path" ]; then
        version=$($py_path --version 2>&1 || echo "unknown")
        echo "  $py_path -> $version"
    fi
done
echo ""

echo "=== Searching for Development Packages ==="
echo ""

# Search for make packages
echo "Make/Build Tools:"
pkg list -a | grep -E "(make|build)" | grep -v SUNWsprot | sort | while read -r line; do
    pkg_name=$(echo "$line" | awk '{print $1}')
    echo "  $pkg_name"
done
echo ""

# Search for compiler packages  
echo "Compilers:"
pkg list -a | grep -E "(gcc|compiler)" | sort | while read -r line; do
    pkg_name=$(echo "$line" | awk '{print $1}')
    echo "  $pkg_name"
done
echo ""

# Search for library packages
echo "Libraries:"
echo "  Compression Libraries:"
pkg list -a | grep -E "(zlib|bzip|compress)" | sort | while read -r line; do
    pkg_name=$(echo "$line" | awk '{print $1}')
    echo "    $pkg_name"
done
echo ""

echo "  Interface Libraries:"
pkg list -a | grep -E "(readline|ncurses|curses)" | sort | while read -r line; do
    pkg_name=$(echo "$line" | awk '{print $1}')
    echo "    $pkg_name"
done
echo ""

echo "  FFI and SSL Libraries:"
pkg list -a | grep -E "(ffi|ssl|crypto)" | sort | while read -r line; do
    pkg_name=$(echo "$line" | awk '{print $1}')
    echo "    $pkg_name"
done
echo ""

# Search for Python packages
echo "Python Runtime:"
pkg list -a | grep -E "runtime/python" | sort | while read -r line; do
    pkg_name=$(echo "$line" | awk '{print $1}')
    status=$(echo "$line" | awk '{print $3}')
    echo "  $pkg_name ($status)"
done
echo ""

echo "Python Development:"
pkg list -a | grep -E "developer/python" | sort | while read -r line; do
    pkg_name=$(echo "$line" | awk '{print $1}')
    status=$(echo "$line" | awk '{print $3}')
    echo "  $pkg_name ($status)"
done
echo ""

# Search for developer groups
echo "Developer Package Groups:"
pkg list -a | grep -E "group.*developer" | sort | while read -r line; do
    pkg_name=$(echo "$line" | awk '{print $1}')
    echo "  $pkg_name"
done
echo ""

echo "=== Package Installation Commands ==="
echo ""
echo "To install development essentials:"
echo "  sudo pkg install developer/build/gnu-make"
echo "  sudo pkg install developer/gcc"
echo "  sudo pkg install library/zlib"
echo "  sudo pkg install library/readline"
echo "  sudo pkg install library/ncurses"
echo "  sudo pkg install compress/bzip2"
echo "  sudo pkg install library/libffi"
echo ""
echo "To install Python (RECOMMENDED - much newer than OpenCSW):"
echo "  sudo pkg install runtime/python-313  # Python 3.13 (latest)"
echo "  sudo pkg install runtime/python-312  # Python 3.12"
echo "  sudo pkg install runtime/python-311  # Python 3.11"
echo "  sudo pkg install runtime/python-310  # Python 3.10"
echo "  sudo pkg install runtime/python-39   # Python 3.9"
echo "  sudo pkg install runtime/python-38   # Python 3.8"
echo ""
echo "To install Python development tools:"
echo "  sudo pkg install developer/python/python-313"
echo "  sudo pkg install developer/python/python-312"
echo "  sudo pkg install developer/python/python-311"
echo "  sudo pkg install developer/python/python-310"
echo ""
echo "To install developer groups (may include multiple tools):"
pkg list -a | grep -E "group.*developer" | head -3 | while read -r line; do
    pkg_name=$(echo "$line" | awk '{print $1}')
    echo "  sudo pkg install $pkg_name"
done
echo ""

echo "=== Check Installed Packages ==="
echo "To see what's already installed:"
echo "  pkg list | grep -E '(make|gcc|python|zlib|readline)'"
echo ""
echo "To get package information:"
echo "  pkg info <package-name>"
echo ""
echo "To see package contents:"
echo "  pkg contents <package-name>"
