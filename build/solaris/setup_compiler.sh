#!/bin/bash

# Solaris C++ Compiler Setup Script
# This script sets up the C++ compiler environment needed for Python package builds
# Can be run standalone or sourced into other scripts

echo "=== Solaris C++ Compiler Setup ==="

# Function to install the latest available GCC
install_latest_gcc() {
    echo "🔍 Detecting package manager and available GCC versions..."
    
    local gcc_installed=false
    local attempted_packages=()
    
    # Check if we're on Solaris 11+ with IPS
    if command -v pkg >/dev/null 2>&1; then
        echo "✓ Found IPS package manager (pkg)"
        
        # Get list of available GCC packages, sorted by version (newest first)
        echo "Searching for available GCC packages..."
        # First get all GCC packages, then sort them properly by version number
        available_gcc_raw=$(pkg list -a 'developer/gcc*' 2>/dev/null | egrep 'developer/gcc-[0-9]')
        
        if [ -n "$available_gcc_raw" ]; then
            # Extract version numbers and sort them properly
            
            # Parse the actual version number from the second column and sort by major version
            # Input format: developer/gcc-14    14.1.0-11.4.62.0.1.74.0    i--
            # Input format: developer/gcc-53    5.3.0-11.4.27.0.1.74.0     i--
            available_gcc=$(echo "$available_gcc_raw" | while IFS= read -r line; do
                if [ -n "$line" ]; then
                    # Extract the actual version number (second field)
                    version_field=$(echo "$line" | awk '{print $2}')
                    # Extract major version from version string (everything before first dot)
                    major_version=$(echo "$version_field" | sed 's/\([0-9][0-9]*\)\..*/\1/')
                    echo "$major_version $line"
                fi
            done | sort -nr | head -10 | sed 's/^[0-9][0-9]* //')
        else
            available_gcc=""
        fi
        
        if [ -n "$available_gcc" ]; then
            echo "Available GCC packages (sorted by version):"
            echo "$available_gcc"
            echo ""
            
            # Extract package names and try to install them (newest first)
            while IFS= read -r line; do
                if [ -n "$line" ]; then
                    pkg_name=$(echo "$line" | awk '{print $1}')
                    if [ -n "$pkg_name" ] && echo "$pkg_name" | egrep '^developer/gcc-[0-9]+$' >/dev/null; then
                        echo "🔧 Attempting to install: $pkg_name"
                        attempted_packages+=("$pkg_name")
                        
                        install_output=$(sudo pkg install --accept "$pkg_name" 2>&1)
                        install_status=$?
                        
                        if [ $install_status -eq 0 ]; then
                            echo "✅ Successfully installed $pkg_name"
                            gcc_installed=true
                            break
                        elif echo "$install_output" | grep -q "No updates necessary"; then
                            echo "✅ $pkg_name already installed"
                            gcc_installed=true
                            break
                        elif echo "$install_output" | grep -q "No matching package"; then
                            echo "⚠ Package $pkg_name not available in this repository"
                            continue
                        else
                            echo "⚠ Failed to install $pkg_name: $(echo "$install_output" | head -2)"
                            continue
                        fi
                    fi
                fi
            done <<< "$available_gcc"
        else
            echo "⚠ No GCC packages found in IPS repositories"
        fi
        
        # If no versioned GCC worked, try generic developer tools
        if [ "$gcc_installed" = false ]; then
            echo "🔧 Trying to install basic developer tools..."
            for pkg in "developer/gcc" "system/header" "developer/build/make"; do
                echo "Attempting to install: $pkg"
                if sudo pkg install --accept "$pkg" 2>/dev/null; then
                    echo "✅ Successfully installed $pkg"
                    gcc_installed=true
                else
                    echo "⚠ Failed to install $pkg"
                fi
            done
        fi
    fi
    
    # Try OpenCSW if IPS didn't work or isn't available
    if [ "$gcc_installed" = false ] && [ -f /opt/csw/bin/pkgutil ]; then
        echo "✓ Found OpenCSW package manager"
        
        # Update package database first
        echo "🔄 Updating OpenCSW package database..."
        sudo /opt/csw/bin/pkgutil -U 2>/dev/null || echo "⚠ Could not update package database"
        
        # Get list of available GCC packages (newest first)
        echo "Searching for available GCC packages in OpenCSW..."
        # First get all GCC packages, then sort them properly by version number
        available_csw_gcc_raw=$(/opt/csw/bin/pkgutil -a 2>/dev/null | egrep '^gcc[0-9]+')
        
        if [ -n "$available_csw_gcc_raw" ]; then
            echo "Raw CSW GCC packages found:"
            echo "$available_csw_gcc_raw"
            echo ""
            
            # Parse the actual version number and sort by major version
            # OpenCSW format typically shows package name and version info
            available_csw_gcc=$(echo "$available_csw_gcc_raw" | while IFS= read -r line; do
                if [ -n "$line" ]; then
                    # Try to extract version info from the line - OpenCSW format varies
                    # Look for version patterns like "12.2.0" or "5.3.0" in the line
                    version_info=$(echo "$line" | sed 's/.*\([0-9][0-9]*\)\.\([0-9][0-9]*\)\.\([0-9][0-9]*\).*/\1/')
                    if [ "$version_info" != "$line" ]; then
                        # Found a version pattern
                        echo "$version_info $line"
                    else
                        # Fallback: extract number from package name (gcc12 -> 12, gcc53 -> 5)
                        pkg_num=$(echo "$line" | sed 's/^gcc\([0-9][0-9]*\).*/\1/')
                        if [ "$pkg_num" -gt 20 ]; then
                            # Likely major.minor encoded (53 = 5.3, so use 5)
                            major_ver=$(echo "$pkg_num" | sed 's/\(.\).*/\1/')
                            echo "$major_ver $line"
                        else
                            # Regular major version
                            echo "$pkg_num $line"
                        fi
                    fi
                fi
            done | sort -nr | head -10 | sed 's/^[0-9][0-9]* //')
            
            echo "Sorted CSW GCC packages (newest first):"
            echo "$available_csw_gcc"
            echo ""
        else
            available_csw_gcc=""
        fi
        
        if [ -n "$available_csw_gcc" ]; then
            echo "Available CSW GCC packages (sorted by version):"
            echo "$available_csw_gcc"
            echo ""
            
            # Try to install GCC packages (newest first)
            while IFS= read -r line; do
                if [ -n "$line" ]; then
                    pkg_name=$(echo "$line" | awk '{print $1}')
                    if [ -n "$pkg_name" ] && echo "$pkg_name" | egrep '^gcc[0-9]+$' >/dev/null; then
                        echo "🔧 Attempting to install CSW package: $pkg_name"
                        attempted_packages+=("$pkg_name")
                        
                        if sudo /opt/csw/bin/pkgutil -y -i "$pkg_name" 2>/dev/null; then
                            echo "✅ Successfully installed CSW $pkg_name"
                            gcc_installed=true
                            
                            # Also try to install corresponding g++ package
                            gxx_pkg="${pkg_name}g++"
                            echo "🔧 Also installing: $gxx_pkg"
                            sudo /opt/csw/bin/pkgutil -y -i "$gxx_pkg" 2>/dev/null || echo "⚠ Could not install $gxx_pkg (may not exist)"
                            break
                        else
                            echo "⚠ Failed to install CSW $pkg_name"
                            continue
                        fi
                    fi
                fi
            done <<< "$available_csw_gcc"
        else
            echo "⚠ No GCC packages found in OpenCSW"
        fi
        
        # Try generic packages if versioned ones failed
        if [ "$gcc_installed" = false ]; then
            echo "🔧 Trying to install basic CSW development tools..."
            for pkg in "gcc" "gpp" "gmake"; do
                echo "Attempting to install CSW: $pkg"
                if sudo /opt/csw/bin/pkgutil -y -i "$pkg" 2>/dev/null; then
                    echo "✅ Successfully installed CSW $pkg"
                    gcc_installed=true
                else
                    echo "⚠ Failed to install CSW $pkg"
                fi
            done
        fi
    elif [ "$gcc_installed" = false ]; then
        echo "⚠ OpenCSW not found - trying to install it first..."
        
        # Try to install OpenCSW
        if command -v pkgadd >/dev/null 2>&1; then
            echo "🔧 Installing OpenCSW package manager..."
            if curl -s http://get.opencsw.org/now | sudo pkgadd -d - all 2>/dev/null; then
                echo "✅ OpenCSW installed successfully"
                
                # Initialize OpenCSW
                export PATH="/opt/csw/bin:$PATH"
                if [ -f /opt/csw/bin/pkgutil ]; then
                    echo "🔄 Updating OpenCSW package database..."
                    sudo /opt/csw/bin/pkgutil -U 2>/dev/null
                    
                    # Try to install GCC via OpenCSW
                    echo "🔧 Installing GCC via OpenCSW..."
                    for pkg in "gcc13" "gcc12" "gcc11" "gcc10" "gcc"; do
                        if sudo /opt/csw/bin/pkgutil -y -i "$pkg" 2>/dev/null; then
                            echo "✅ Successfully installed CSW $pkg"
                            gcc_installed=true
                            break
                        fi
                    done
                fi
            else
                echo "⚠ Failed to install OpenCSW"
            fi
        else
            echo "⚠ pkgadd not available - cannot install OpenCSW"
        fi
    fi
    
    # Update PATH and hash after installation
    if [ "$gcc_installed" = true ]; then
        echo "🔄 Updating environment after GCC installation..."
        
        # Add common GCC installation paths to PATH
        export PATH="/usr/gcc/bin:/usr/gcc/*/bin:/opt/csw/bin:/opt/csw/gcc*/bin:/usr/local/bin:$PATH"
        hash -r  # Clear command hash
        
        echo "✅ GCC installation completed successfully"
        echo "📦 Attempted packages: ${attempted_packages[*]}"
        echo "🔄 Updated PATH to include GCC directories"
        return 0
    else
        echo "❌ Failed to install any GCC packages"
        echo "📦 Attempted packages: ${attempted_packages[*]}"
        return 1
    fi
}

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
    
    # Update PATH to include common GCC installation locations
    export PATH="/usr/gcc/bin:/usr/gcc/*/bin:/opt/csw/bin:/opt/csw/gcc*/bin:/usr/local/bin:$PATH"
    hash -r  # Clear command cache
    
    # Comprehensive search for C++ compilers (prefer newer versions)
    compiler_search_paths=(
        # Versioned compilers (newest first)
        "g++-14" "g++-13" "g++-12" "g++-11" "g++-10" "g++-9" "g++-8" "g++-7"
        # IPS GCC installations
        "/usr/gcc/14/bin/g++" "/usr/gcc/13/bin/g++" "/usr/gcc/12/bin/g++" 
        "/usr/gcc/11/bin/g++" "/usr/gcc/10/bin/g++" "/usr/gcc/9/bin/g++"
        "/usr/gcc/8/bin/g++" "/usr/gcc/7/bin/g++"
        # OpenCSW installations
        "/opt/csw/gcc14/bin/g++" "/opt/csw/gcc13/bin/g++" "/opt/csw/gcc12/bin/g++"
        "/opt/csw/gcc11/bin/g++" "/opt/csw/gcc10/bin/g++" "/opt/csw/gcc9/bin/g++"
        "/opt/csw/bin/g++-14" "/opt/csw/bin/g++-13" "/opt/csw/bin/g++-12"
        "/opt/csw/bin/g++-11" "/opt/csw/bin/g++-10" "/opt/csw/bin/g++-9"
        "/opt/csw/bin/g++" 
        # Glob patterns for GCC installations
        "/usr/gcc/*/bin/g++" "/usr/local/bin/g++*" "/opt/csw/bin/g++*"
        # Generic fallback
        "g++"
    )
    
    echo "Scanning compiler search paths..."
    for cxx_candidate in "${compiler_search_paths[@]}"; do
        # Handle glob patterns
        if echo "$cxx_candidate" | grep '\*' >/dev/null; then
            # Expand glob and process each match
            for expanded_path in $cxx_candidate; do
                if [ -x "$expanded_path" ]; then
                    echo "  Checking: $expanded_path"
                    if echo 'int main(){return 0;}' | "$expanded_path" -x c++ - -o /tmp/test_cxx_$$ 2>/dev/null; then
                        rm -f /tmp/test_cxx_$$
                        echo "✓ Found working C++ compiler: $expanded_path"
                        cpp_compiler_found="$expanded_path"
                        break 2  # Break out of both loops
                    else
                        echo "  ✗ $expanded_path exists but doesn't work"
                    fi
                fi
            done
        else
            # Direct command check
            if command -v "$cxx_candidate" >/dev/null 2>&1; then
                echo "  Checking: $cxx_candidate ($(which $cxx_candidate))"
                # Test if this compiler works
                if echo 'int main(){return 0;}' | "$cxx_candidate" -x c++ - -o /tmp/test_cxx_$$ 2>/dev/null; then
                    rm -f /tmp/test_cxx_$$
                    echo "✓ Found working C++ compiler: $cxx_candidate"
                    cpp_compiler_found="$cxx_candidate"
                    break
                else
                    echo "  ✗ $cxx_candidate found but doesn't work"
                fi
            fi
        fi
    done
    
    # Find corresponding C compiler if we found a C++ compiler
    if [ -n "$cpp_compiler_found" ]; then
        echo "✓ Found C++ compiler: $cpp_compiler_found"
        echo "Looking for corresponding C compiler..."
        
        # Find corresponding C compiler
        cxx_dir=$(dirname "$cpp_compiler_found" 2>/dev/null || echo "/usr/bin")
        cxx_base=$(basename "$cpp_compiler_found")
        
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
        
        # Comprehensive search for C compiler
        c_search_paths=(
            "$cxx_dir/$gcc_candidate"
            "$(which $gcc_candidate 2>/dev/null)"
            "$cxx_dir/gcc"
            "gcc-14" "gcc-13" "gcc-12" "gcc-11" "gcc-10" "gcc-9" "gcc-8" "gcc-7"
            "/usr/gcc/*/bin/gcc" "/opt/csw/bin/gcc*" "/opt/csw/gcc*/bin/gcc"
            "gcc"
        )
        
        for gcc_path in "${c_search_paths[@]}"; do
            if [ -n "$gcc_path" ] && [ "$gcc_path" != "null" ]; then
                # Handle glob patterns for C compiler too
                if echo "$gcc_path" | grep '\*' >/dev/null; then
                    for expanded_gcc in $gcc_path; do
                        if [ -x "$expanded_gcc" ]; then
                            echo "  Testing C compiler: $expanded_gcc"
                            if echo 'int main(){return 0;}' | "$expanded_gcc" -x c - -o /tmp/test_cc_$$ 2>/dev/null; then
                                rm -f /tmp/test_cc_$$
                                echo "✓ Found working C compiler: $expanded_gcc"
                                c_compiler_found="$expanded_gcc"
                                break 2
                            fi
                        fi
                    done
                elif command -v "$gcc_path" >/dev/null 2>&1; then
                    echo "  Testing C compiler: $gcc_path"
                    if echo 'int main(){return 0;}' | "$gcc_path" -x c - -o /tmp/test_cc_$$ 2>/dev/null; then
                        rm -f /tmp/test_cc_$$
                        echo "✓ Found working C compiler: $gcc_path"
                        c_compiler_found="$gcc_path"
                        break
                    fi
                fi
            fi
        done
    fi
    
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
        echo "🔧 Attempting to automatically install the latest available GCC..."
        
        # Try to install compilers automatically
        if install_latest_gcc; then
            echo "✓ GCC installation completed, re-scanning for compilers..."
            
            # Clear the previous search results
            cpp_compiler_found=""
            c_compiler_found=""
            
            # Re-run the compiler search after installation
            echo "🔍 Re-scanning for compilers after installation..."
            
            # Update PATH again to ensure new installations are found
            export PATH="/usr/gcc/bin:/usr/gcc/*/bin:/opt/csw/bin:/opt/csw/gcc*/bin:/usr/local/bin:$PATH"
            hash -r
            
            # Re-run the compiler search logic
            echo "Searching for C++ compilers on Solaris..."
            
            # Comprehensive search for C++ compilers (prefer newer versions)  
            compiler_search_paths=(
                # Versioned compilers (newest first)
                "g++-14" "g++-13" "g++-12" "g++-11" "g++-10" "g++-9" "g++-8" "g++-7"
                # IPS GCC installations
                "/usr/gcc/14/bin/g++" "/usr/gcc/13/bin/g++" "/usr/gcc/12/bin/g++" 
                "/usr/gcc/11/bin/g++" "/usr/gcc/10/bin/g++" "/usr/gcc/9/bin/g++"
                "/usr/gcc/8/bin/g++" "/usr/gcc/7/bin/g++"
                # OpenCSW installations
                "/opt/csw/gcc14/bin/g++" "/opt/csw/gcc13/bin/g++" "/opt/csw/gcc12/bin/g++"
                "/opt/csw/gcc11/bin/g++" "/opt/csw/gcc10/bin/g++" "/opt/csw/gcc9/bin/g++"
                "/opt/csw/bin/g++-14" "/opt/csw/bin/g++-13" "/opt/csw/bin/g++-12"
                "/opt/csw/bin/g++-11" "/opt/csw/bin/g++-10" "/opt/csw/bin/g++-9"
                "/opt/csw/bin/g++" 
                # Glob patterns for GCC installations
                "/usr/gcc/*/bin/g++" "/usr/local/bin/g++*" "/opt/csw/bin/g++*"
                # Generic fallback
                "g++"
            )
            
            echo "Post-installation compiler scan..."
            for cxx_candidate in "${compiler_search_paths[@]}"; do
                # Handle glob patterns
                if echo "$cxx_candidate" | grep '\*' >/dev/null; then
                    # Expand glob and process each match
                    for expanded_path in $cxx_candidate; do
                        if [ -x "$expanded_path" ]; then
                            echo "  Checking: $expanded_path"
                            if echo 'int main(){return 0;}' | "$expanded_path" -x c++ - -o /tmp/test_cxx_post_$$ 2>/dev/null; then
                                rm -f /tmp/test_cxx_post_$$
                                echo "✅ Found working C++ compiler: $expanded_path"
                                cpp_compiler_found="$expanded_path"
                                break 2  # Break out of both loops
                            fi
                        fi
                    done
                else
                    # Direct command check
                    if command -v "$cxx_candidate" >/dev/null 2>&1; then
                        echo "  Checking: $cxx_candidate ($(which $cxx_candidate))"
                        if echo 'int main(){return 0;}' | "$cxx_candidate" -x c++ - -o /tmp/test_cxx_post_$$ 2>/dev/null; then
                            rm -f /tmp/test_cxx_post_$$
                            echo "✅ Found working C++ compiler: $cxx_candidate"
                            cpp_compiler_found="$cxx_candidate"
                            break
                        fi
                    fi
                fi
            done
            
            # Find corresponding C compiler if we found a C++ compiler
            if [ -n "$cpp_compiler_found" ]; then
                echo "Looking for corresponding C compiler for: $cpp_compiler_found"
                
                cxx_dir=$(dirname "$cpp_compiler_found" 2>/dev/null || echo "/usr/bin")
                cxx_base=$(basename "$cpp_compiler_found")
                
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
                
                # Search for C compiler
                c_search_paths=(
                    "$cxx_dir/$gcc_candidate"
                    "$(which $gcc_candidate 2>/dev/null)"
                    "$cxx_dir/gcc"
                    "gcc-14" "gcc-13" "gcc-12" "gcc-11" "gcc-10" "gcc-9" "gcc-8" "gcc-7"
                    "/usr/gcc/*/bin/gcc" "/opt/csw/bin/gcc*" "/opt/csw/gcc*/bin/gcc"
                    "gcc"
                )
                
                for gcc_path in "${c_search_paths[@]}"; do
                    if [ -n "$gcc_path" ] && [ "$gcc_path" != "null" ]; then
                        if echo "$gcc_path" | grep '\*' >/dev/null; then
                            for expanded_gcc in $gcc_path; do
                                if [ -x "$expanded_gcc" ]; then
                                    if echo 'int main(){return 0;}' | "$expanded_gcc" -x c - -o /tmp/test_cc_post_$$ 2>/dev/null; then
                                        rm -f /tmp/test_cc_post_$$
                                        echo "✅ Found working C compiler: $expanded_gcc"
                                        c_compiler_found="$expanded_gcc"
                                        break 2
                                    fi
                                fi
                            done
                        elif command -v "$gcc_path" >/dev/null 2>&1; then
                            if echo 'int main(){return 0;}' | "$gcc_path" -x c - -o /tmp/test_cc_post_$$ 2>/dev/null; then
                                rm -f /tmp/test_cc_post_$$
                                echo "✅ Found working C compiler: $gcc_path"
                                c_compiler_found="$gcc_path"
                                break
                            fi
                        fi
                    fi
                done
            fi
            
            # Check if we found compilers after installation
            if [ -n "$cpp_compiler_found" ] && [ -n "$c_compiler_found" ]; then
                echo "✅ Successfully found compilers after installation!"
                # Set up the compiler environment for the newly found compilers
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
                if echo 'int main(){return 0;}' | "$CXX" -x c++ - -o /tmp/final_test_post_$$ 2>/dev/null; then
                    rm -f /tmp/final_test_post_$$
                    echo "✓ Compiler test passed - ready for Python builds"
                    return 0
                else
                    echo "⚠ Warning: Compiler test failed even after installation"
                    return 1
                fi
            else
                echo "❌ Still no working compilers found even after installation"
                echo "Debug info:"
                echo "  cpp_compiler_found: '$cpp_compiler_found'"
                echo "  c_compiler_found: '$c_compiler_found'"
                echo "  PATH: $(echo "$PATH" | cut -d: -f1-5)"
                echo "Available executables in common paths:"
                for path in /usr/gcc/*/bin /opt/csw/bin /usr/local/bin; do
                    if [ -d "$path" ]; then
                        echo "  $path: $(ls "$path"/g* 2>/dev/null | head -3 | tr '\n' ' ')"
                    fi
                done
                return 1
            fi
        else
            echo "✗ Failed to automatically install GCC"
            echo "⚠ You may need to manually install GCC development tools"
            echo ""
            echo "Try installing with one of these commands:"
            echo "  sudo pkg install developer/gcc-13  # For Solaris 11 with IPS"
            echo "  sudo /opt/csw/bin/pkgutil -y -i gcc13  # For OpenCSW"
            return 1
        fi
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
