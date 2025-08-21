#!/bin/bash

# OpenCSW Installation Guide for NCPA Solaris Build
# This script provides the correct OpenCSW installation commands

echo "=== OpenCSW Installation Guide for NCPA ==="
echo "Date: $(date)"
echo ""

echo "=== Step 1: Install and Update OpenCSW ==="
echo "pkgadd -d http://get.opencsw.org/now"
echo "/opt/csw/bin/pkgutil -U"
echo ""

echo "=== Step 2: Install Core System Dependencies ==="
echo "Core compiler and build tools:"
echo "/opt/csw/bin/pkgutil -y -i gcc4core"
echo "/opt/csw/bin/pkgutil -y -i gcc4g++"
echo "/opt/csw/bin/pkgutil -y -i make"
echo ""

echo "Core libraries:"
echo "/opt/csw/bin/pkgutil -y -i zlib"
echo "/opt/csw/bin/pkgutil -y -i openssl"
echo "/opt/csw/bin/pkgutil -y -i libffi"
echo "/opt/csw/bin/pkgutil -y -i ggettext"
echo ""

echo "=== Step 3: Install Python ==="
echo "Try these Python options (in order of preference):"
echo "/opt/csw/bin/pkgutil -y -i python3"
echo "# or"
echo "/opt/csw/bin/pkgutil -y -i python39"
echo "# or"
echo "/opt/csw/bin/pkgutil -y -i python38"
echo ""

echo "=== Step 4: Install Python-specific Packages ==="
echo "These are the correct OpenCSW package names for Python modules:"
echo "/opt/csw/bin/pkgutil -y -i py_openssl      # for pyOpenSSL"
echo "/opt/csw/bin/pkgutil -y -i py_cryptography # for cryptography"
echo "/opt/csw/bin/pkgutil -y -i py_cffi         # for cffi"
echo "/opt/csw/bin/pkgutil -y -i py_requests     # for requests (if available)"
echo "/opt/csw/bin/pkgutil -y -i py_jinja2       # for Jinja2 (if available)"
echo "/opt/csw/bin/pkgutil -y -i py_psutil       # for psutil (if available)"
echo ""

echo "=== Step 5: Verify Installation ==="
echo "Check installed packages:"
echo "/opt/csw/bin/pkgutil -l | grep py_"
echo ""
echo "List files from a package (example):"
echo "/usr/sbin/pkgchk -L CSWpy-openssl"
echo ""

echo "=== Current System Status ==="
if command -v /opt/csw/bin/pkgutil >/dev/null 2>&1; then
    echo "✓ OpenCSW is installed"
    echo ""
    echo "Python packages currently installed:"
    /opt/csw/bin/pkgutil -l | grep -E "^py_|^python" || echo "No Python packages found"
    echo ""
    echo "Available Python packages in catalog:"
    /opt/csw/bin/pkgutil -a | grep -E "^py_|^python" | head -10 || echo "No Python packages available"
else
    echo "✗ OpenCSW not installed"
    echo "Run: pkgadd -d http://get.opencsw.org/now"
fi

echo ""
echo "=== Troubleshooting ==="
echo "If packages are not found:"
echo "1. Update catalog: /opt/csw/bin/pkgutil -U"
echo "2. Search for alternative names: /opt/csw/bin/pkgutil -a | grep <package>"
echo "3. Check available Python versions: /opt/csw/bin/pkgutil -a | grep python"
echo ""
echo "Common package name patterns:"
echo "- System libraries: openssl, zlib, libffi"
echo "- Python modules: py_<modulename> (e.g., py_openssl)"
echo "- Development packages: <package>_dev or <package>-dev"
