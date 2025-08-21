#!/bin/bash

# Get version and architecture
if command -v realpath >/dev/null 2>&1; then
    realpath_cmd="realpath"
elif command -v grealpath >/dev/null 2>&1; then
    realpath_cmd="grealpath"
else
    echo "ERROR: Neither realpath nor grealpath command found."
    echo "Please install GNU coreutils or ensure realpath is available."
    exit 1
fi

DIR=$(dirname "$(readlink -f "$0")")
BUILD_DIR=$($realpath_cmd "$DIR/..")
VERSION=$(cat $BUILD_DIR/../VERSION)
ARCH=$(arch)

echo "Building Solaris package for NCPA version $VERSION on $ARCH architecture"

# Set up package info - fix the sed commands
echo "Setting up package information..."
sed "s/VERSION=.*/VERSION=$VERSION/" $DIR/pkginfo > $DIR/pkginfo.tmp
sed "s/ARCH=.*/ARCH=$ARCH/" $DIR/pkginfo.tmp > $BUILD_DIR/pkginfo
rm -rf $DIR/pkginfo.tmp

# Make the package and cleanup
(
    cd $BUILD_DIR

    echo "Cleaning up old packages..."
    rm -f ncpa*.pkg

    echo "Preparing package files..."
    
    # Verify ncpa directory exists
    if [ ! -d "ncpa" ]; then
        echo "ERROR: ncpa directory not found in $BUILD_DIR"
        echo "Available directories:"
        ls -la
        echo "Looking for ncpa-* directories..."
        ls -la ncpa-* 2>/dev/null || echo "No ncpa-* directories found"
        exit 1
    fi
    
    # Add package information/scripts to current directory (where pkgmk runs)
    # pkginfo goes into the ncpa directory for the package content
    cp pkginfo ncpa/pkginfo
    
    # Copy the manual start script to the package for installation
    echo "Adding manual start script to package..."
    mkdir -p ncpa/usr/local/bin
    cp solaris/ncpa-start.sh ncpa/usr/local/bin/ncpa-start.sh
    chmod +x ncpa/usr/local/bin/ncpa-start.sh
    
    # Install scripts stay in current directory for pkgmk to find them
    cp solaris/postinstall ./postinstall
    cp solaris/preinstall ./preinstall  
    cp solaris/preremove ./preremove

    echo "Creating prototype file..."
    # Add prototype file
    echo 'i pkginfo' > prototype
    echo 'i postinstall' >> prototype
    echo 'i preinstall' >> prototype
    echo 'i preremove' >> prototype
    
    # Generate file list for the package
    echo "Generating file list..."
    if command -v pkgproto >/dev/null 2>&1; then
        pkgproto ncpa >> prototype
        echo "✓ Prototype file created successfully"
        echo "Verifying install scripts exist in current directory:"
        echo "  preinstall: $([ -f preinstall ] && echo "✓ EXISTS" || echo "✗ MISSING")"
        echo "  postinstall: $([ -f postinstall ] && echo "✓ EXISTS" || echo "✗ MISSING")"
        echo "  preremove: $([ -f preremove ] && echo "✓ EXISTS" || echo "✗ MISSING")"
        echo "  pkginfo: $([ -f ncpa/pkginfo ] && echo "✓ EXISTS" || echo "✗ MISSING")"
        echo "First 10 lines of prototype file:"
        head -10 prototype
    else
        echo "ERROR: pkgproto command not found."
        echo "Please ensure Solaris packaging tools are installed."
        exit 1
    fi

    echo "Building package..."
    # Build package and create the .pkg file
    if command -v pkgmk >/dev/null 2>&1; then
        echo "Running pkgmk to build package..."
        if pkgmk -o -b $(pwd); then
            echo "✓ pkgmk completed successfully"
        else
            echo "ERROR: pkgmk failed with exit code $?"
            echo "Check prototype file and ensure all referenced files exist:"
            cat prototype
            exit 1
        fi
    else
        echo "ERROR: pkgmk command not found."
        echo "Please ensure Solaris packaging tools are installed."
        exit 1
    fi
    
    if command -v pkgtrans >/dev/null 2>&1; then
        echo "Running pkgtrans to create final package..."
        if pkgtrans -s /var/spool/pkg ncpa-$VERSION.$ARCH.pkg ncpa; then
            echo "✓ pkgtrans completed successfully"
            # Check if the package file was actually created
            if [ -f "/var/spool/pkg/ncpa-$VERSION.$ARCH.pkg" ]; then
                echo "✓ Package file found, moving to build directory..."
                mv -f /var/spool/pkg/ncpa-$VERSION.$ARCH.pkg .
                if [ -f "ncpa-$VERSION.$ARCH.pkg" ]; then
                    echo "✓ Package successfully moved to: $(pwd)/ncpa-$VERSION.$ARCH.pkg"
                else
                    echo "ERROR: Failed to move package to current directory"
                    exit 1
                fi
            else
                echo "ERROR: Package file was not created: /var/spool/pkg/ncpa-$VERSION.$ARCH.pkg"
                echo "Available files in /var/spool/pkg:"
                ls -la /var/spool/pkg/ 2>/dev/null || echo "Cannot list /var/spool/pkg/"
                exit 1
            fi
        else
            echo "ERROR: pkgtrans failed with exit code $?"
            exit 1
        fi
    else
        echo "ERROR: pkgtrans command not found."
        echo "Please ensure Solaris packaging tools are installed."
        exit 1
    fi

    echo "Cleaning up build artifacts..."
    # Remove build leftovers
    rm -rf /var/spool/pkg/ncpa
    rm -f prototype
    rm -f pkginfo
    # Remove install scripts from current directory (not from ncpa/)
    rm -f postinstall
    rm -f preinstall
    rm -f preremove
    # Remove pkginfo from ncpa directory
    rm -f ncpa/pkginfo

    echo "Package created successfully: ncpa-$VERSION.$ARCH.pkg"
)
