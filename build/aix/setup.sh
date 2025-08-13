#!/bin/bash -e

# AIX-specific setup for NCPA build
# Integrates with virtual environment manager when available

# Virtual environment integration variables
VENV_MANAGER="${BUILD_DIR}/venv_manager.sh"
VENV_NAME="${VENV_NAME:-ncpa-build}"

# Check if using virtual environment or fallback to system Python
if [[ "$SKIP_PYTHON" == "1" ]]; then
    echo "***** aix/setup.sh - Using virtual environment mode"
    # Python will be provided by venv_manager, no system Python needed
else
    echo "***** aix/setup.sh - Fallback mode - detecting system Python"
    PYTHONBIN=$(which python3)
fi

# Automatically install Python requirements in venv after setup
if [ -n "$VENV_MANAGER" ] && [ -x "$VENV_MANAGER" ]; then
    "$VENV_MANAGER" install-requirements
fi

update_py_packages() {
    # Check if we're in virtual environment mode
    if [[ -n "$VENV_MANAGER" && -n "$VENV_NAME" && "$SKIP_PYTHON" == "1" ]]; then
        echo "    - Using virtual environment approach via venv_manager"
        if ! "$VENV_MANAGER" install_packages; then
            echo "ERROR! Failed to install Python packages via venv_manager"
            return 1
        fi
        
        # Get the virtual environment Python executable
        local venv_python=$("$VENV_MANAGER" get_python_path)
        if [[ -z "$venv_python" ]]; then
            echo "ERROR! Could not get virtual environment Python path"
            return 1
        fi
        
        # Update our Python commands to use the venv Python
        export PYTHONBIN="$venv_python"
        echo "    - Updated PYTHONBIN to virtual environment: $PYTHONBIN"
    else
        echo "    - Using legacy system Python approach"
        echo "Skipping update packages, manually update them with:"
        echo "$PYTHONBIN -m pip install -r $BUILD_DIR/resources/require.txt --upgrade"
    fi
}
