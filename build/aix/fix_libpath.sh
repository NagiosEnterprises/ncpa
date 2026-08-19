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

aix_ar_t() {
    # AIX ar wants a traditional key (t). GNU-style -t treats the archive as a member.
    ar -X64 t "$1" 2>/dev/null
}

ensure_aix_member() {
    archive=$1
    need=$2
    alt=$3
    if aix_ar_t "$archive" | grep -qx "$need"; then
        echo "  $archive has member $need"
        return 0
    fi
    if [ -n "$alt" ] && aix_ar_t "$archive" | grep -qx "$alt"; then
        tmpdir=/tmp/ncpa-ar.$$
        rm -rf "$tmpdir"
        mkdir -p "$tmpdir"
        echo "  Adding member $need to $archive from $alt"
        (
            cd "$tmpdir" || exit 1
            ar -X64 x "$archive" "$alt"
            cp "$alt" "$need"
            ar -X64 r "$archive" "$need"
        )
        rm -rf "$tmpdir"
        if aix_ar_t "$archive" | grep -qx "$need"; then
            return 0
        fi
    fi
    echo "ERROR: $archive is missing 64-bit member $need"
    echo "Members: $(aix_ar_t "$archive" | tr '\n' ' ')"
    return 1
}

replace_libgcc_from_compiler_dir() {
    dest="$NCPA_ROOT/lib/libgcc_s.a"
    for src in /opt/freeware/lib/gcc/*/*/libgcc_s.a \
               /opt/freeware/lib64/gcc/*/*/libgcc_s.a; do
        [ -e "$src" ] || continue
        echo "  Replacing libgcc_s.a with GCC runtime archive $src"
        cp -f "$src" "$dest"
        if aix_ar_t "$dest" | grep -qx 'shr.o'; then
            return 0
        fi
        if ensure_aix_member "$dest" "shr.o" "libgcc_s.so.1"; then
            return 0
        fi
    done
    return 1
}

if command -v ar >/dev/null 2>&1; then
    echo "***** aix/fix_libpath.sh - verifying required archive members"
    if ! aix_ar_t "$NCPA_ROOT/lib/libgcc_s.a" | grep -qx 'shr.o'; then
        replace_libgcc_from_compiler_dir || \
            ensure_aix_member "$NCPA_ROOT/lib/libgcc_s.a" "shr.o" "libgcc_s.so.1" || exit 1
    else
        echo "  $NCPA_ROOT/lib/libgcc_s.a has member shr.o"
    fi    ensure_aix_member "$NCPA_ROOT/lib/libiconv.a" "libiconv.so.2" "libiconv.so.1" || exit 1
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