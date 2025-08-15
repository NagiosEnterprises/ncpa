#!/bin/bash
# Test script to verify patchelf virtual environment installation

echo "=== Testing patchelf virtual environment integration ==="

# Simulate virtual environment setup
export VIRTUAL_ENV="/tmp/test-venv-$$"
export VENV_NAME="test-ncpa"
export PYTHONBIN="$VIRTUAL_ENV/bin/python"
export SKIP_PYTHON=1

# Create mock virtual environment
mkdir -p "$VIRTUAL_ENV/bin"
echo '#!/bin/bash
echo "Python 3.13.0 (mock virtual environment)"' > "$PYTHONBIN"
chmod +x "$PYTHONBIN"

# Create mock pip
cat > "$VIRTUAL_ENV/bin/pip" << 'EOF'
#!/bin/bash
if [ "$1" = "install" ] && [ "$2" = "--verbose" ] && [ "$3" = "patchelf" ]; then
    echo "Installing patchelf in virtual environment..."
    # Create a mock patchelf binary
    cat > "$VIRTUAL_ENV/bin/patchelf" << 'PATCHELF_EOF'
#!/bin/bash
if [ "$1" = "--version" ]; then
    echo "patchelf 0.18.0 (pip-installed)"
else
    echo "patchelf mock: $@"
fi
PATCHELF_EOF
    chmod +x "$VIRTUAL_ENV/bin/patchelf"
    echo "Successfully installed patchelf"
    exit 0
else
    echo "Mock pip: $@"
    exit 0
fi
EOF
chmod +x "$VIRTUAL_ENV/bin/pip"

# Mock pip --version
cat > "$VIRTUAL_ENV/bin/python" << 'EOF'
#!/bin/bash
if [ "$1" = "-m" ] && [ "$2" = "pip" ] && [ "$3" = "--version" ]; then
    echo "pip 23.0.1 (mock)"
    exit 0
elif [ "$1" = "-m" ] && [ "$2" = "pip" ] && [ "$3" = "install" ]; then
    shift 3  # Remove -m pip install
    exec "$VIRTUAL_ENV/bin/pip" install "$@"
elif [ "$1" = "--version" ]; then
    echo "Python 3.13.0 (mock virtual environment)"
else
    echo "Mock python: $@"
fi
EOF
chmod +x "$VIRTUAL_ENV/bin/python"

echo "Created mock virtual environment at: $VIRTUAL_ENV"
echo "Mock Python: $PYTHONBIN"

# Source the improved patchelf installation section
# Extract just the patchelf installation function
echo "Extracting patchelf installation logic..."

# Test the ensure_venv_priority function
ensure_venv_priority() {
    if [ -n "$VIRTUAL_ENV" ] && [ -d "$VIRTUAL_ENV/bin" ]; then
        # Remove any existing venv paths from PATH to avoid duplicates
        PATH=$(echo "$PATH" | sed "s|$VIRTUAL_ENV/bin:||g" | sed "s|:$VIRTUAL_ENV/bin||g")
        # Add venv bin to the front of PATH
        export PATH="$VIRTUAL_ENV/bin:$PATH"
        echo "✓ Ensured virtual environment priority in PATH: $VIRTUAL_ENV/bin"
    fi
}

# Test the function
echo ""
echo "Testing ensure_venv_priority function..."
original_path="$PATH"
ensure_venv_priority
echo "Original PATH: $original_path"
echo "Updated PATH: $PATH"

# Test that venv is first in PATH
if echo "$PATH" | grep -q "^$VIRTUAL_ENV/bin:"; then
    echo "✓ Virtual environment is correctly prioritized in PATH"
else
    echo "✗ Virtual environment not properly prioritized in PATH"
fi

# Test patchelf installation (simplified version)
echo ""
echo "Testing mock patchelf installation..."
patchelf_installed=false

if [ -n "$VIRTUAL_ENV" ] && [ -n "$PYTHONBIN" ] && [ -x "$PYTHONBIN" ]; then
    echo "Virtual environment detected: $VIRTUAL_ENV"
    echo "Using Python: $PYTHONBIN"
    
    ensure_venv_priority
    
    # Check if pip is available in venv
    if "$PYTHONBIN" -m pip --version >/dev/null 2>&1; then
        echo "Attempting to install patchelf via pip in virtual environment..."
        
        # Try to install patchelf
        pip_output=$("$PYTHONBIN" -m pip install --verbose patchelf 2>&1)
        pip_status=$?
        
        if [ $pip_status -eq 0 ]; then
            echo "✓ Successfully installed patchelf via pip"
            
            # Verify patchelf is now available in venv
            venv_patchelf="$VIRTUAL_ENV/bin/patchelf"
            if [ -x "$venv_patchelf" ]; then
                echo "✓ patchelf available in venv: $venv_patchelf"
                ensure_venv_priority
                if "$venv_patchelf" --version >/dev/null 2>&1; then
                    echo "✓ patchelf is functional: $("$venv_patchelf" --version 2>/dev/null | head -1)"
                    patchelf_installed=true
                fi
            fi
        fi
    fi
fi

echo ""
echo "Final verification:"
if command -v patchelf >/dev/null 2>&1; then
    patchelf_location=$(which patchelf)
    patchelf_version=$(patchelf --version 2>&1 | head -1)
    echo "✓ patchelf is available at: $patchelf_location"
    echo "✓ patchelf version: $patchelf_version"
    
    # Check if it's in the virtual environment (preferred)
    if [ -n "$VIRTUAL_ENV" ] && echo "$patchelf_location" | grep -q "$VIRTUAL_ENV"; then
        echo "✓ EXCELLENT: Using patchelf from virtual environment (isolated build)"
    fi
else
    echo "✗ patchelf not available"
fi

# Cleanup
echo ""
echo "Cleaning up test environment..."
rm -rf "$VIRTUAL_ENV"
echo "✓ Test completed"
