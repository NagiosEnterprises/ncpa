#!/bin/bash

echo "=== Python Detection Debug Script ==="
echo ""

echo "Environment Variables:"
echo "  PYTHONBIN: ${PYTHONBIN:-'(not set)'}"
echo "  PATH: $PATH"
echo ""

echo "Available Python Installations:"
for py_path in /usr/bin/python* /opt/csw/bin/python* /usr/local/bin/python*; do
    if [ -x "$py_path" ]; then
        version=$($py_path --version 2>&1 || echo "unknown")
        echo "  $py_path -> $version"
    fi
done
echo ""

echo "Python in PATH:"
if command -v python3 >/dev/null 2>&1; then
    echo "  python3: $(which python3) -> $(python3 --version 2>&1)"
else
    echo "  python3: not found"
fi

if command -v python >/dev/null 2>&1; then
    echo "  python: $(which python) -> $(python --version 2>&1)"
else
    echo "  python: not found"
fi
echo ""

echo "Library Paths for cx_Freeze:"
if [ -x "${PYTHONBIN:-python3}" ]; then
    echo "Using Python: ${PYTHONBIN:-python3}"
    ${PYTHONBIN:-python3} -c "
import sys
print(f'  Python executable: {sys.executable}')
print(f'  Python version: {sys.version}')
print(f'  Python paths: {sys.path[:3]}...')

try:
    import os
    import glob
    actual_python_version = f'{sys.version_info.major}.{sys.version_info.minor}'
    print(f'  Detected version: {actual_python_version}')
    
    # Look for Python library
    for search_path in ['/usr/lib', '/usr/local/lib', '/opt/csw/lib']:
        matches = glob.glob(f'{search_path}/libpython{actual_python_version}.so*')
        if matches:
            print(f'  Python library found: {matches[0]}')
            break
    else:
        print(f'  Python library NOT found for version {actual_python_version}')
except Exception as e:
    print(f'  Error detecting libraries: {e}')
"
else
    echo "  No Python available for library detection"
fi
echo ""

echo "cx_Freeze Test:"
if [ -x "${PYTHONBIN:-python3}" ]; then
    ${PYTHONBIN:-python3} -c "
try:
    import cx_Freeze
    print('  cx_Freeze: Available')
    print(f'  cx_Freeze version: {cx_Freeze.version}')
except ImportError as e:
    print(f'  cx_Freeze: NOT available - {e}')
except Exception as e:
    print(f'  cx_Freeze: Error - {e}')
"
else
    echo "  No Python available for cx_Freeze test"
fi
