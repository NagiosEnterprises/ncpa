#!/bin/bash

# Solaris Package Debug Script
# This script helps identify what Python packages are available on a Solaris system

echo "=== Solaris Package Debug Information ==="
echo "Date: $(date)"
echo "System: $(uname -a)"
echo ""

echo "=== Checking Package Managers ==="
echo -n "pkg (Solaris 11+): "
if command -v pkg >/dev/null 2>&1; then
    echo "Available"
    echo "Checking for Python packages in pkg..."
    pkg list | grep python || echo "No Python packages found in pkg"
else
    echo "Not available"
fi

echo ""
echo -n "pkgutil (OpenCSW): "
if command -v /opt/csw/bin/pkgutil >/dev/null 2>&1; then
    echo "Available"
    echo "Checking for required packages in OpenCSW..."
    echo "=== Core Build Dependencies ==="
    for pkg in gcc4core gcc ggettext gettext zlib libz libffi ffi; do
        if /opt/csw/bin/pkgutil -a | grep -q "^$pkg "; then
            echo "✓ $pkg - Available"
        else
            echo "✗ $pkg - Not found"
        fi
    done
    
    echo ""
    echo "=== Python-specific Packages ==="
    for pkg in py_openssl py_cryptography py_cffi; do
        if /opt/csw/bin/pkgutil -a | grep -q "^$pkg "; then
            echo "✓ $pkg - Available"
        else
            echo "✗ $pkg - Not found"
        fi
    done
    
    echo ""
    echo "=== Python Packages ==="
    for pkg in python3 python39 python38 python37 python36; do
        if /opt/csw/bin/pkgutil -a | grep -q "^$pkg "; then
            echo "✓ $pkg - Available"
        else
            echo "✗ $pkg - Not found"
        fi
    done
    
    echo ""
    echo "=== Python-related packages (first 10) ==="
    /opt/csw/bin/pkgutil -a | grep -i python | head -10 || echo "No Python packages found"
else
    echo "Not available - installing..."
    if pkgadd -d http://get.opencsw.org/now; then
        echo "OpenCSW installed successfully"
        /opt/csw/bin/pkgutil -U
        echo "Python packages available:"
        /opt/csw/bin/pkgutil -a | grep python | head -10
    else
        echo "Failed to install OpenCSW"
    fi
fi

echo ""
echo "=== Existing Python Installations ==="
for py_path in \
    "/usr/bin/python" \
    "/usr/bin/python2" \
    "/usr/bin/python3" \
    "/usr/local/bin/python" \
    "/usr/local/bin/python3" \
    "/opt/csw/bin/python" \
    "/opt/csw/bin/python2" \
    "/opt/csw/bin/python3"; do
    
    if [ -x "$py_path" ]; then
        echo -n "$py_path: "
        $py_path --version 2>&1 || echo "version check failed"
    fi
done

echo ""
echo "=== All Python Executables ==="
find /usr/bin /usr/local/bin /opt/csw/bin -name "python*" -executable 2>/dev/null | sort

echo ""
echo "=== System Information ==="
echo "Solaris Version: $(cat /etc/release 2>/dev/null | head -1 || echo 'Unknown')"
echo "Architecture: $(arch)"
echo "Kernel: $(uname -r)"

echo ""
echo "=== End Debug Information ==="
