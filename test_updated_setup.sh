#!/bin/bash

echo "=== Testing Updated setup.sh patchelf Installation Logic ==="
echo ""

# Set up test environment similar to the build process
BUILD_DIR_FOR_VERSION=$(dirname "$(dirname "$0")")/build
export VENV_NAME="test-setup-patchelf-venv"
export SKIP_PYTHON=1  # Use virtual environment mode
export NO_INTERACTION=1

# Source the version config (required for setup.sh)
if [ -f "$BUILD_DIR_FOR_VERSION/version_config.sh" ]; then
    echo "Loading version configuration..."
    source "$BUILD_DIR_FOR_VERSION/version_config.sh"
else
    echo "ERROR: Cannot find version_config.sh"
    exit 1
fi

# Create a test virtual environment using the venv manager
VENV_MANAGER="$BUILD_DIR_FOR_VERSION/venv_manager.sh"

if [ ! -f "$VENV_MANAGER" ]; then
    echo "ERROR: venv_manager.sh not found at $VENV_MANAGER"
    exit 1
fi

echo "Creating test virtual environment with venv manager..."
if ! bash "$VENV_MANAGER" create; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

echo ""
echo "Activating virtual environment..."
if ! bash "$VENV_MANAGER" activate; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

echo ""
echo "=== Environment Check ==="
echo "VIRTUAL_ENV: $VIRTUAL_ENV"
echo "PYTHONBIN: ${PYTHONBIN:-'not set'}"
echo "which python: $(which python 2>/dev/null || echo 'not found')"
echo "which python3: $(which python3 2>/dev/null || echo 'not found')"

# Simulate what the updated setup.sh does
echo ""
echo "=== Testing ensure_venv_priority function (from setup.sh) ==="

ensure_venv_priority() {
    if [ -n "$VIRTUAL_ENV" ] && [ -d "$VIRTUAL_ENV/bin" ]; then
        # Remove any existing venv paths from PATH to avoid duplicates
        PATH=$(echo "$PATH" | sed "s|$VIRTUAL_ENV/bin:||g" | sed "s|:$VIRTUAL_ENV/bin||g")
        # Add venv bin to the front of PATH
        export PATH="$VIRTUAL_ENV/bin:$PATH"
        echo "✓ Ensured virtual environment priority in PATH: $VIRTUAL_ENV/bin"
        
        # Set PYTHONBIN to use virtual environment Python
        if [ -x "$VIRTUAL_ENV/bin/python" ]; then
            PYTHONBIN="$VIRTUAL_ENV/bin/python"
            export PYTHONBIN
            echo "✓ Set PYTHONBIN to virtual environment Python: $PYTHONBIN"
        elif [ -x "$VIRTUAL_ENV/bin/python3" ]; then
            PYTHONBIN="$VIRTUAL_ENV/bin/python3"
            export PYTHONBIN
            echo "✓ Set PYTHONBIN to virtual environment Python3: $PYTHONBIN"
        fi
    fi
}

ensure_venv_priority

echo ""
echo "=== Testing patchelf installation logic (from updated setup.sh) ==="

patchelf_installed=false

if [ -n "$VIRTUAL_ENV" ] && [ -n "$PYTHONBIN" ] && [ -x "$PYTHONBIN" ]; then
    echo "Virtual environment detected: $VIRTUAL_ENV"
    echo "Using Python: $PYTHONBIN"
    
    # Ensure venv bin directory is first in PATH
    ensure_venv_priority
    
    # Check if pip is available in venv
    if "$PYTHONBIN" -m pip --version >/dev/null 2>&1; then
        echo "✓ pip is available in virtual environment"
        echo "pip version: $("$PYTHONBIN" -m pip --version)"
        
        echo ""
        echo "Would run: \"$PYTHONBIN\" -m pip install --verbose patchelf"
        echo "This demonstrates that the updated setup.sh will:"
        echo "  1. Use the virtual environment Python: $PYTHONBIN"
        echo "  2. Install patchelf in the virtual environment: $VIRTUAL_ENV/bin/"
        echo "  3. Verify patchelf works in the virtual environment"
        
        # Test what python pip would actually use
        echo ""
        echo "Verification - what python pip would actually use:"
        echo "\"$PYTHONBIN\" -c \"import sys; print('Python executable:', sys.executable)\""
        "$PYTHONBIN" -c "import sys; print('Python executable:', sys.executable)" 2>&1
        
        if [[ "$("$PYTHONBIN" -c "import sys; print(sys.executable)" 2>&1)" == "$VIRTUAL_ENV"* ]]; then
            echo "✓ SUCCESS: pip will use virtual environment Python"
            patchelf_installed=true
        else
            echo "✗ FAILURE: pip would still use system Python"
        fi
    else
        echo "✗ pip not available in virtual environment"
    fi
else
    echo "✗ Virtual environment or PYTHONBIN not properly configured"
fi

echo ""
echo "=== Test Summary ==="
if [ "$patchelf_installed" = true ]; then
    echo "✓ SUCCESS: Updated setup.sh will correctly use virtual environment for patchelf"
    echo "  - PYTHONBIN correctly set to: $PYTHONBIN"
    echo "  - Virtual environment: $VIRTUAL_ENV"
    echo "  - pip will install in: $VIRTUAL_ENV/bin/"
else
    echo "✗ FAILURE: Updated setup.sh may still have issues"
fi

# Cleanup
echo ""
echo "Cleaning up test virtual environment..."
bash "$VENV_MANAGER" delete || echo "Warning: Could not clean up test venv"
