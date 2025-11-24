#!/bin/bash

# Solaris Zlib Detection Script
# This script helps identify available compression libraries on Solaris

echo "=== Solaris Zlib/Compression Library Detection ==="
echo "Date: $(date)"
echo "System: $(uname -a)"
echo ""

echo "=== Checking System Libraries ==="
echo "Looking for zlib in standard locations..."

# Check common library paths
lib_paths=("/usr/lib" "/lib" "/usr/local/lib" "/opt/csw/lib" "/usr/sfw/lib")
zlib_found=false

for path in "${lib_paths[@]}"; do
    if [ -d "$path" ]; then
        echo "Checking $path..."
        zlib_files=$(find "$path" -name "*libz*" -o -name "*zlib*" 2>/dev/null)
        if [ -n "$zlib_files" ]; then
            echo "  Found: $zlib_files"
            zlib_found=true
        else
            echo "  No zlib libraries found"
        fi
    fi
done

echo ""
echo "=== Checking Header Files ==="
include_paths=("/usr/include" "/usr/local/include" "/opt/csw/include")
zlib_headers=false

for path in "${include_paths[@]}"; do
    if [ -d "$path" ]; then
        echo "Checking $path for zlib.h..."
        if [ -f "$path/zlib.h" ]; then
            echo "  ✓ Found zlib.h in $path"
            zlib_headers=true
        else
            echo "  ✗ No zlib.h found in $path"
        fi
    fi
done

echo ""
echo "=== Package Manager Availability ==="

# Check pkg (Solaris 11+)
echo -n "Solaris pkg manager: "
if command -v pkg >/dev/null 2>&1; then
    echo "Available"
    echo "Checking for zlib packages..."
    pkg list | grep -i zlib || echo "No zlib packages found via pkg"
else
    echo "Not available"
fi

echo ""
# Check OpenCSW
echo -n "OpenCSW pkgutil: "
if command -v /opt/csw/bin/pkgutil >/dev/null 2>&1; then
    echo "Available"
    echo "Checking for zlib/compression packages..."
    /opt/csw/bin/pkgutil -a | grep -E "(zlib|libz|compress)" || echo "No zlib packages found via OpenCSW"
else
    echo "Not available"
fi

echo ""
echo "=== Compiler Test ==="
echo "Testing if zlib can be used for compilation..."

# Create a simple test program
cat > /tmp/zlib_test.c << 'EOF'
#include <stdio.h>
#include <zlib.h>

int main() {
    printf("zlib version: %s\n", zlibVersion());
    return 0;
}
EOF

# Try to compile with different compiler options
if command -v gcc >/dev/null 2>&1; then
    echo "Testing with gcc..."
    if gcc -o /tmp/zlib_test /tmp/zlib_test.c -lz 2>/dev/null; then
        echo "✓ gcc can compile and link with zlib"
        /tmp/zlib_test 2>/dev/null || echo "Compiled but failed to run"
    else
        echo "✗ gcc cannot compile with zlib"
    fi
elif command -v /opt/csw/bin/gcc >/dev/null 2>&1; then
    echo "Testing with CSW gcc..."
    if /opt/csw/bin/gcc -o /tmp/zlib_test /tmp/zlib_test.c -lz 2>/dev/null; then
        echo "✓ CSW gcc can compile and link with zlib"
        /tmp/zlib_test 2>/dev/null || echo "Compiled but failed to run"
    else
        echo "✗ CSW gcc cannot compile with zlib"
    fi
else
    echo "No gcc compiler found"
fi

# Cleanup
rm -f /tmp/zlib_test.c /tmp/zlib_test

echo ""
echo "=== Summary ==="
if [ "$zlib_found" = true ]; then
    echo "✓ Zlib libraries found on system"
else
    echo "✗ No zlib libraries found"
fi

if [ "$zlib_headers" = true ]; then
    echo "✓ Zlib headers found"
else
    echo "✗ No zlib headers found"
fi

echo ""
echo "=== Recommendations ==="
if [ "$zlib_found" = false ] || [ "$zlib_headers" = false ]; then
    echo "1. Try installing via Solaris pkg: 'pkg install library/zlib'"
    echo "2. Try installing via OpenCSW: 'pkgutil -i zlib'"
    echo "3. Consider manual compilation from source"
else
    echo "Zlib appears to be available on the system"
fi
