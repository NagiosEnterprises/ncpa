#!/bin/bash

# Quick OpenCSW Package Checker for NCPA Build
# This script checks if the required packages are available before attempting installation

echo "=== OpenCSW Package Availability Check ==="

if [ ! -f /opt/csw/bin/pkgutil ]; then
    echo "OpenCSW not installed. Installing..."
    pkgadd -d http://get.opencsw.org/now
    /opt/csw/bin/pkgutil -U
fi

echo "Checking required packages..."

# Function to check package availability
check_pkg() {
    local pkg="$1"
    local desc="$2"
    if /opt/csw/bin/pkgutil -a | grep -q "^$pkg "; then
        echo "✓ $pkg ($desc) - Available"
        return 0
    else
        echo "✗ $pkg ($desc) - Not available"
        return 1
    fi
}

# Check core dependencies
echo ""
echo "=== Core Build Dependencies ==="
available_count=0
total_count=0

packages=(
    "gcc4core:GCC compiler core"
    "gcc:GCC compiler" 
    "gcc4:GCC compiler v4"
    "ggettext:GNU gettext"
    "gettext:gettext"
    "zlib:zlib compression"
    "libz:zlib library"
    "zlib1:zlib version 1"
    "libzlib:zlib library alternative"
    "zlib_dev:zlib development"
    "libz_dev:zlib development alternative"
    "libffi:FFI library"
    "ffi:FFI"
    "libffi_dev:FFI development"
)

for pkg_info in "${packages[@]}"; do
    pkg="${pkg_info%%:*}"
    desc="${pkg_info##*:}"
    if check_pkg "$pkg" "$desc"; then
        ((available_count++))
    fi
    ((total_count++))
done

echo ""
echo "=== Python Packages ==="
python_available=false
python_packages=("python3:Python 3" "python39:Python 3.9" "python38:Python 3.8" "python37:Python 3.7" "python36:Python 3.6")

for pkg_info in "${python_packages[@]}"; do
    pkg="${pkg_info%%:*}"
    desc="${pkg_info##*:}"
    if check_pkg "$pkg" "$desc"; then
        python_available=true
    fi
done

echo ""
echo "=== Summary ==="
echo "Core dependencies: $available_count/$total_count available"
if [ "$python_available" = true ]; then
    echo "Python: At least one Python package available"
else
    echo "Python: No Python packages found"
fi

if [ $available_count -gt 0 ] && [ "$python_available" = true ]; then
    echo "✓ Sufficient packages available for build"
    exit 0
else
    echo "✗ Insufficient packages available"
    echo ""
    echo "Available Python packages:"
    /opt/csw/bin/pkgutil -a | grep -i python || echo "None found"
    exit 1
fi
