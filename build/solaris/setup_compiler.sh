#!/bin/bash

# Solaris C++ Compiler Setup Script
# This script sets up the C++ compiler environment needed for Python package builds
# Can be run standalone or sourced into other scripts

echo "=== Solaris C++ Compiler Setup ==="

# Function to find and set up compilers
setup_solaris_compilers() {
    local cpp_compiler_found=""
    local c_compiler_found=""
    
    # First, check if we already have working compilers
    if command -v g++ >/dev/null 2>&1 && command -v gcc >/dev/null 2>&1; then
        echo "✓ Found g++ and gcc in PATH"
        # Test if they work
        if echo 'int main(){return 0;}' | g++ -x c++ - -o /tmp/test_cpp_$$  2>/dev/null; then
            rm -f /tmp/test_cpp_$$
            echo "✓ g++ is working - using existing compilers"
            export CC="gcc"
            export CXX="g++"
            echo "✓ Set CC=$CC, CXX=$CXX"
            return 0
        else
            echo "⚠ g++ found but not working properly"
        fi
    fi
    
    echo "Searching for C++ compilers on Solaris..."
    
    # Search for C++ compilers (prefer newer versions)
    for cxx_candidate in g++-14 g++-13 g++-12 g++-11 g++-10 g++-9 g++-8 g++-7 /usr/gcc/*/bin/g++ /usr/local/bin/g++* /opt/csw/bin/g++* g++; do
        if command -v "$cxx_candidate" >/dev/null 2>&1; then
            # Test if this compiler works
            if echo 'int main(){return 0;}' | "$cxx_candidate" -x c++ - -o /tmp/test_cxx_$$ 2>/dev/null; then
                rm -f /tmp/test_cxx_$$
                echo "✓ Found working C++ compiler: $cxx_candidate"
                cpp_compiler_found="$cxx_candidate"
                
                # Find corresponding C compiler
                cxx_dir=$(dirname "$cxx_candidate" 2>/dev/null || echo "/usr/bin")
                cxx_base=$(basename "$cxx_candidate")
                
                # Try to find matching C compiler
                case "$cxx_base" in
                    g++-*)
                        version_suffix="${cxx_base#g++-}"
                        gcc_candidate="gcc-$version_suffix"
                        ;;
                    g++)
                        gcc_candidate="gcc"
                        ;;
                    *)
                        gcc_candidate="gcc"
                        ;;
                esac
                
                # Look for C compiler in same directory first, then in PATH
                for gcc_path in "$cxx_dir/$gcc_candidate" "$(which $gcc_candidate 2>/dev/null)" "gcc"; do
                    if [ -n "$gcc_path" ] && command -v "$gcc_path" >/dev/null 2>&1; then
                        if echo 'int main(){return 0;}' | "$gcc_path" -x c - -o /tmp/test_cc_$$ 2>/dev/null; then
                            rm -f /tmp/test_cc_$$
                            echo "✓ Found working C compiler: $gcc_path"
                            c_compiler_found="$gcc_path"
                            break
                        fi
                    fi
                done
                
                if [ -n "$c_compiler_found" ]; then
                    break  # Found both compilers
                fi
            fi
        fi
    done
    
    # If we found compilers, set them up
    if [ -n "$cpp_compiler_found" ] && [ -n "$c_compiler_found" ]; then
        echo "✓ Setting up compiler environment:"
        echo "  CC=$c_compiler_found"
        echo "  CXX=$cpp_compiler_found"
        
        export CC="$c_compiler_found"
        export CXX="$cpp_compiler_found"
        
        # Also set compiler flags for Python builds
        export CFLAGS="-fPIC"
        export CXXFLAGS="-fPIC -std=c++11"
        export LDFLAGS=""
        
        # Make sure the compiler paths are in PATH
        cpp_dir=$(dirname "$cpp_compiler_found")
        if [ -n "$cpp_dir" ] && [ "$cpp_dir" != "/usr/bin" ]; then
            export PATH="$cpp_dir:$PATH"
        fi
        
        echo "✓ C++ compiler environment configured successfully"
        
        # Test the setup
        echo "Testing compiler setup..."
        if echo 'int main(){return 0;}' | "$CXX" -x c++ - -o /tmp/final_test_$$ 2>/dev/null; then
            rm -f /tmp/final_test_$$
            echo "✓ Compiler test passed - ready for Python builds"
        else
            echo "⚠ Warning: Compiler test failed"
            return 1
        fi
        
        return 0
    else
        echo "✗ No working C/C++ compilers found"
        echo "⚠ You may need to install GCC development tools"
        echo ""
        echo "Try installing with one of these commands:"
        echo "  sudo pkg install developer/gcc-13  # For Solaris 11 with IPS"
        echo "  sudo /opt/csw/bin/pkgutil -y -i gcc13  # For OpenCSW"
        return 1
    fi
}

# Run the setup
setup_solaris_compilers

# If successful, show current environment
if [ $? -eq 0 ]; then
    echo ""
    echo "=== Current Compiler Environment ==="
    echo "CC=$CC"
    echo "CXX=$CXX"
    echo "CFLAGS=$CFLAGS"
    echo "CXXFLAGS=$CXXFLAGS"
    echo "PATH (first few entries): $(echo "$PATH" | cut -d: -f1-3)"
    echo "===================================="
    echo ""
    echo "✓ Ready for Python package compilation"
    echo "  These environment variables are now exported"
    echo "  Source this script to set up environment in other shells:"
    echo "    source $(realpath "$0")"
fi
