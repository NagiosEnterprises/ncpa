#!/bin/bash -e
#
# Post-freeze AIX helper: ensure bundled runtime libs exist and rewrite
# absolute /opt/freeware XCOFF import paths so NCPA runs standalone from
# /usr/local/ncpa/lib (see GitHub issue #1421).
#
# Usage: fix_libpath.sh /path/to/ncpa
#

NCPA_ROOT="${1:-}"
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd -P)
FIX_PY="$SCRIPT_DIR/fix_xcoff_imports.py"
TARGET_LIBPATH="/usr/local/ncpa/lib:/usr/lib:/lib"

REQUIRED_LIBS="libpython3.12.a libgcc_s.a libintl.a libiconv.a libsqlite3.a libz.a libffi.a"

if [ -z "$NCPA_ROOT" ]; then
    echo "Usage: $0 /path/to/ncpa"
    exit 1
fi

if [ ! -d "$NCPA_ROOT" ]; then
    echo "ERROR: NCPA root directory not found: $NCPA_ROOT"
    exit 1
fi

if [ ! -f "$NCPA_ROOT/ncpa" ]; then
    echo "ERROR: NCPA binary not found at $NCPA_ROOT/ncpa"
    exit 1
fi

if [ ! -f "$FIX_PY" ]; then
    echo "ERROR: Missing $FIX_PY"
    exit 1
fi

PYTHONBIN="${PYTHONBIN:-python3}"
if ! command -v "$PYTHONBIN" >/dev/null 2>&1; then
    PYTHONBIN=python3.12
fi

echo "***** aix/fix_libpath.sh - verifying bundled runtime libraries"
missing=0
for lib in $REQUIRED_LIBS; do
    if [ -f "$NCPA_ROOT/lib/$lib" ]; then
        echo "  Found $NCPA_ROOT/lib/$lib"
    else
        echo "  Missing $NCPA_ROOT/lib/$lib"
        missing=1
    fi
done

if [ "$missing" -ne 0 ]; then
    echo "ERROR: Required AIX runtime libraries were not bundled into $NCPA_ROOT/lib"
    echo "Expected: $REQUIRED_LIBS"
    exit 1
fi

if command -v ar >/dev/null 2>&1; then
    echo "***** aix/fix_libpath.sh - verifying required archive members"
    if ! ar -X64 -t "$NCPA_ROOT/lib/libgcc_s.a" 2>/dev/null | grep -qx 'shr.o'; then
        echo "ERROR: $NCPA_ROOT/lib/libgcc_s.a is missing 64-bit member shr.o"
        echo "Members: $(ar -X64 -t "$NCPA_ROOT/lib/libgcc_s.a" 2>/dev/null | tr '\n' ' ')"
        echo "Copy the GCC runtime archive (often under /opt/freeware/lib*/gcc/*/*/libgcc_s.a)."
        exit 1
    fi
    if ! ar -X64 -t "$NCPA_ROOT/lib/libiconv.a" 2>/dev/null | grep -qx 'libiconv.so.2'; then
        echo "ERROR: $NCPA_ROOT/lib/libiconv.a is missing 64-bit member libiconv.so.2"
        echo "Members: $(ar -X64 -t "$NCPA_ROOT/lib/libiconv.a" 2>/dev/null | tr '\n' ' ')"
        exit 1
    fi
fi

echo "***** aix/fix_libpath.sh - rewriting absolute freeware import paths"
TARGETS="$NCPA_ROOT/ncpa"
for lib in $REQUIRED_LIBS; do
    TARGETS="$TARGETS $NCPA_ROOT/lib/$lib"
done

# Also rewrite any other shipped archives/shared objects under lib/
for extra in "$NCPA_ROOT"/lib/*.a "$NCPA_ROOT"/lib/*.so*; do
    if [ -f "$extra" ]; then
        case " $TARGETS " in
            *" $extra "*) ;;
            *) TARGETS="$TARGETS $extra" ;;
        esac
    fi
done

$PYTHONBIN "$FIX_PY" --libpath "$TARGET_LIBPATH" --fail-on-freeware $TARGETS

echo "***** aix/fix_libpath.sh - verifying with dump -Tv (if available)"
if command -v dump >/dev/null 2>&1; then
    for target in $TARGETS; do
        hits=$(dump -Tv "$target" 2>/dev/null | grep '/opt/freeware/' || true)
        if [ -n "$hits" ]; then
            # Embedded LIBPATH may still mention freeware directories; import IDs
            # with basenames were already rejected by fix_xcoff_imports.py.
            echo "  NOTE: dump -Tv mentions /opt/freeware in $target (non-fatal if only LIBPATH):"
            echo "$hits" | sed 's/^/    /'
        fi
    done
else
    echo "  dump not available; skipped dump -Tv verification"
fi

echo "***** aix/fix_libpath.sh - completed successfully"
echo "Standalone check after install:"
echo "  LIBPATH=/usr/local/ncpa/lib /usr/local/ncpa/ncpa --version"
echo "  dump -Tv /usr/local/ncpa/lib/libpython3.12.a | grep freeware  # expect empty"
echo "  startsrc -s ncpa"