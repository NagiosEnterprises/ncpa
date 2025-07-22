#!/bin/bash

echo "=== GNU Make Package Diagnostics for Solaris 11 ==="
echo ""

# Check current system
echo "System Information:"
echo "  OS: $(uname -sr)"
echo "  Architecture: $(arch)"
echo ""

# Check for existing make installations
echo "Existing make installations:"
for dir in /usr/bin /usr/sfw/bin /usr/ccs/bin /opt/csw/bin /usr/local/bin; do
    if [ -d "$dir" ]; then
        find "$dir" -name "*make*" -executable 2>/dev/null | while read -r makefile; do
            echo "  $makefile -> $($makefile --version 2>&1 | head -1 | cut -d' ' -f1-3 2>/dev/null || echo 'version unknown')"
        done
    fi
done
echo ""

# Check PATH
echo "Current PATH:"
echo "$PATH" | tr ':' '\n' | while read -r dir; do
    echo "  $dir"
done
echo ""

# Check OpenCSW
echo "OpenCSW Package Manager:"
if [ -f /opt/csw/bin/pkgutil ]; then
    echo "  ✓ OpenCSW installed"
    echo "  Available make-related packages:"
    /opt/csw/bin/pkgutil -a | grep -i make | head -10
else
    echo "  ✗ OpenCSW not installed"
fi
echo ""

# Check IPS (native Solaris)
echo "IPS (Native Solaris) Package Manager:"
if command -v pkg >/dev/null 2>&1; then
    echo "  ✓ IPS available"
    echo "  Available make-related packages:"
    pkg list -a | grep -i make | head -10 2>/dev/null || echo "    No make packages found"
    echo ""
    echo "  Available developer packages:"
    pkg list -a | grep "developer/build" | head -10 2>/dev/null || echo "    No developer/build packages found"
else
    echo "  ✗ IPS not available"
fi
echo ""

# Check for development packages
echo "Development Package Groups:"
if command -v pkg >/dev/null 2>&1; then
    echo "  Checking for developer package groups..."
    pkg list -a | grep "group.*developer" 2>/dev/null || echo "    No developer group packages found"
    pkg list -a | grep "build" | grep -v "SUNWsprot" | head -5 2>/dev/null || echo "    No build packages found"
fi
echo ""

echo "=== Recommendations ==="
echo ""
if command -v pkg >/dev/null 2>&1; then
    echo "Try these commands to install make:"
    echo "  sudo pkg install developer/build/gnu-make"
    echo "  sudo pkg install developer/build/make"
    echo "  sudo pkg install group/developer/developer-gnu"
    echo "  sudo pkg install build-essential"
    echo ""
    echo "For readline and ncurses:"
    echo "  sudo pkg install library/readline"
    echo "  sudo pkg install library/ncurses"
    echo "  sudo pkg install library/libedit"
fi

if [ -f /opt/csw/bin/pkgutil ]; then
    echo ""
    echo "Or try OpenCSW:"
    echo "  /opt/csw/bin/pkgutil -i gmake"
    echo "  /opt/csw/bin/pkgutil -i make"
    echo "  /opt/csw/bin/pkgutil -i readline"
    echo "  /opt/csw/bin/pkgutil -i ncurses"
fi

echo ""
echo "You can also check what's already available in the system:"
echo "  which make"
echo "  which gmake"
echo "  find /usr -name '*make*' -executable 2>/dev/null"
echo "  find /usr/lib /lib -name 'libreadline*' 2>/dev/null"
echo "  find /usr/lib /lib -name 'libncurses*' 2>/dev/null"
