#!/bin/bash

echo "=== Python Detection Debug Script ==="
echo ""

echo "Environment Variables:"
echo "  PYTHONBIN: ${PYTHONBIN:-'(not set)'}"
echo "  PATH: $PATH"
echo "  Python environment status:"
if [ -x "${PYTHONBIN:-python3}" ]; then
    ${PYTHONBIN:-python3} -c "
import sys
import sysconfig
import os

# Check if this is a virtual environment
if hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix:
    print('    Virtual environment: Yes')
    print(f'    Base prefix: {sys.base_prefix}')
    print(f'    Current prefix: {sys.prefix}')
elif os.path.exists(os.path.join(sys.prefix, 'pyvenv.cfg')):
    print('    Virtual environment: Yes (detected via pyvenv.cfg)')
else:
    print('    Virtual environment: No')

# Check if externally managed
purelib = sysconfig.get_path('purelib')
if '/usr/lib' in purelib or '/usr/local/lib' in purelib:
    print('    Externally managed: Likely (system-wide installation)')
    print(f'    Package install path: {purelib}')
    
    # Check for EXTERNALLY-MANAGED file (PEP 668)
    externally_managed_file = os.path.join(sysconfig.get_path('stdlib'), 'EXTERNALLY-MANAGED')
    if os.path.exists(externally_managed_file):
        print('    PEP 668 EXTERNALLY-MANAGED: Yes')
        try:
            with open(externally_managed_file, 'r') as f:
                content = f.read()[:200]  # First 200 chars
                print(f'    Content preview: {repr(content)}...')
        except:
            pass
    else:
        print('    PEP 668 EXTERNALLY-MANAGED: No')
else:
    print('    Externally managed: No')
    print(f'    Package install path: {purelib}')
"
else
    echo "    No Python available for environment check"
fi
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
echo ""

echo "Pip Installation Test:"
if [ -x "${PYTHONBIN:-python3}" ]; then
    echo "  Testing pip installation capabilities..."
    ${PYTHONBIN:-python3} -c "
import subprocess
import sys

def test_pip_install():
    test_package = 'requests'  # A common, safe package to test with
    
    # Test different pip install methods
    methods = [
        (['--user'], 'User installation'),
        (['--break-system-packages'], 'Break system packages'),
        ([], 'Direct installation')
    ]
    
    for args, description in methods:
        try:
            # Test with --dry-run to avoid actually installing
            cmd = [sys.executable, '-m', 'pip', 'install', '--dry-run'] + args + [test_package]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f'    {description}: Would work')
            else:
                error = result.stderr.strip()
                if 'externally-managed-environment' in error:
                    print(f'    {description}: Blocked - externally managed environment')
                elif 'permission denied' in error.lower():
                    print(f'    {description}: Blocked - permission denied')
                else:
                    print(f'    {description}: Failed - {error[:100]}...')
        except Exception as e:
            print(f'    {description}: Error testing - {str(e)[:50]}...')

test_pip_install()
"
else
    echo "  No Python available for pip test"
fi
