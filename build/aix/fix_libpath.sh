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

REQUIRED_LIBS="libpython3.12.a libgcc_s.a libstdc++.a libintl.a libiconv.a libsqlite3.a libz.a libffi.a"

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

export OBJECT_MODE=64

aix_ar_t() {
    # AIX ar wants a traditional key (t). GNU-style -t treats the archive as a member.
    ar -X64 t "$1" 2>/dev/null
}

# Newest GCC runtime first (13 before 10). Unmatched globs are skipped by [ -e ].
GCC_LIBGCC_S=""
GCC_LIBSTDCXX=""
for src in /opt/freeware/lib/gcc/*/*/libgcc_s.a /opt/freeware/lib64/gcc/*/*/libgcc_s.a; do
    if [ -e "$src" ]; then
        GCC_LIBGCC_S="$src $GCC_LIBGCC_S"
    fi
done
for src in /opt/freeware/lib/gcc/*/*/libstdc++.a /opt/freeware/lib64/gcc/*/*/libstdc++.a; do
    if [ -e "$src" ]; then
        GCC_LIBSTDCXX="$src $GCC_LIBSTDCXX"
    fi
done

# Copy a Toolbox archive that already has the member ldd wants. Never extract
# and re-ar GCC/GNU shared members: that makes the loader report
# "Cannot find libgcc_s.a(shr.o)" even when ar t still lists the name.
ensure_archive_member() {
    dest=$1
    need=$2
    shift 2

    if [ -f "$dest" ] && aix_ar_t "$dest" | grep -qx "$need"; then
        echo "  Keeping $dest (already has $need)"
        return 0
    fi

    for src in "$@"; do
        [ -e "$src" ] || continue
        members=$(aix_ar_t "$src")
        echo "  Candidate $src members: $(echo "$members" | tr '\n' ' ')"
        if echo "$members" | grep -qx "$need"; then
            echo "  Copying $src -> $dest (has $need)"
            cp -p "$src" "$dest"
            return 0
        fi
    done

    echo "ERROR: $dest is missing 64-bit member $need"
    echo "Looked at: $*"
    return 1
}

echo "***** aix/fix_libpath.sh - ensuring loadable GCC/GNU archives"
ensure_archive_member "$NCPA_ROOT/lib/libgcc_s.a" "shr.o" \
    $GCC_LIBGCC_S \
    /opt/freeware/lib64/libgcc_s.a \
    /opt/freeware/lib/libgcc_s.a || exit 1

ensure_archive_member "$NCPA_ROOT/lib/libstdc++.a" "libstdc++.so.6" \
    $GCC_LIBSTDCXX \
    /opt/freeware/lib64/libstdc++.a \
    /opt/freeware/lib/libstdc++.a || exit 1

ensure_archive_member "$NCPA_ROOT/lib/libiconv.a" "libiconv.so.2" \
    /opt/freeware/lib64/libiconv.a \
    /opt/freeware/lib/libiconv.a || exit 1

# Do not `ar r` IBM libiconv members into the GNU archive. Re-inserting
# members is what made ldd report "Cannot find ... (libiconv.so.2)".
# ksh93 needs IBM shr4_64.o, so never export LIBPATH in the shell; the
# service script applies LIBPATH only to ncpa via env(1).

echo "***** aix/fix_libpath.sh - rewriting Toolbox lib import paths in place"
# /opt/freeware/lib is 17 bytes; /usr/local/ncpa/lib is 19, so those import
# IDs are cleared (empty path = LIBPATH search) instead of same-length
# replaced. Do not extract/`ar r` GCC/GNU iconv shared members.
# Skip GCC runtime archives (BUILD LIBPATH strings). Do not extract/`ar r`.
set -- "$NCPA_ROOT/ncpa"
for f in "$NCPA_ROOT/lib"/*.a; do
    [ -f "$f" ] || continue
    case "$(basename "$f")" in
        libgcc_s.a) continue ;;
    esac
    set -- "$@" "$f"
done
if command -v find >/dev/null 2>&1; then
    for f in $(find "$NCPA_ROOT" -type f \( -name '*.so' -o -name '*.so.*' \) 2>/dev/null); do
        [ -f "$f" ] || continue
        set -- "$@" "$f"
    done
fi
$PYTHONBIN "$FIX_PY" --libpath "$TARGET_LIBPATH" "$@"

echo "***** aix/fix_libpath.sh - archive member check"
echo "  libgcc_s.a members: $(aix_ar_t "$NCPA_ROOT/lib/libgcc_s.a" | tr '\n' ' ')"
echo "  libstdc++.a members: $(aix_ar_t "$NCPA_ROOT/lib/libstdc++.a" | tr '\n' ' ')"
echo "  libiconv.a members: $(aix_ar_t "$NCPA_ROOT/lib/libiconv.a" | tr '\n' ' ')"
if ! aix_ar_t "$NCPA_ROOT/lib/libgcc_s.a" | grep -qx 'shr.o'; then
    echo "ERROR: libgcc_s.a is missing shr.o"
    exit 1
fi
if ! aix_ar_t "$NCPA_ROOT/lib/libstdc++.a" | grep -qx 'libstdc++.so.6'; then
    echo "ERROR: libstdc++.a is missing libstdc++.so.6"
    exit 1
fi
if ! aix_ar_t "$NCPA_ROOT/lib/libiconv.a" | grep -qx 'libiconv.so.2'; then
    echo "ERROR: libiconv.a is missing libiconv.so.2"
    exit 1
fi

echo "***** aix/fix_libpath.sh - verifying stored loader import IDs"
verify_targets="$NCPA_ROOT/ncpa"
for f in \
    "$NCPA_ROOT/lib/libpython3.12.a" \
    "$NCPA_ROOT/lib/libintl.a" \
    "$NCPA_ROOT/lib/libiconv.a"
do
    [ -f "$f" ] && verify_targets="$verify_targets $f"
done
# Fail only when the bundled files still contain dump-style
# path\\0lib*.a\\0member triplets under /opt/freeware. dump -H on a
# Toolbox host can print /opt/freeware/lib for empty/relative imports
# that ldd resolves against the build machine's LIBPATH.
if ! $PYTHONBIN "$FIX_PY" --verify-stored $verify_targets; then
    echo "ERROR: bundled objects still store absolute Toolbox import IDs"
    exit 1
fi

echo "***** aix/fix_libpath.sh - dump -X64 -H (informational on Toolbox hosts)"
if command -v dump >/dev/null 2>&1; then
    for dump_target in $verify_targets; do
        [ -f "$dump_target" ] || continue
        hits=$(dump -X64 -H "$dump_target" 2>/dev/null | grep '/opt/freeware/lib' | grep '\.a' || true)
        if [ -n "$hits" ]; then
            echo "  NOTE: dump -X64 -H still prints Toolbox .a imports in $dump_target:"
            echo "$hits" | sed 's/^/    /'
            echo "  Stored import IDs in that file were already verified clean."
        else
            echo "  $dump_target: dump -X64 -H has no absolute /opt/freeware/lib .a imports"
        fi
    done
else
    echo "  dump not available; skipped dump -X64 -H listing"
fi

echo "***** aix/fix_libpath.sh - completed successfully"
echo "Standalone check after install (do not export LIBPATH in your shell):"
echo "  ldd /usr/local/ncpa/ncpa"
echo "  ar -X64 t /usr/local/ncpa/lib/libgcc_s.a"
echo "  ar -X64 t /usr/local/ncpa/lib/libstdc++.a"
echo "  ar -X64 t /usr/local/ncpa/lib/libiconv.a"
echo "  startsrc -s ncpa"  