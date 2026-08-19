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

export OBJECT_MODE=64

aix_ar_t() {
    # AIX ar wants a traditional key (t). GNU-style -t treats the archive as a member.
    ar -X64 t "$1" 2>/dev/null
}

aix_ar_create() {
    dest=$1
    member=$2
    rm -f "$dest"
    if ar -X64 rcs "$dest" "$member"; then
        return 0
    fi
    if ar -X64 rc "$dest" "$member"; then
        ar -X64 s "$dest" 2>/dev/null || ranlib -X64 "$dest" 2>/dev/null || true
        return 0
    fi
    return 1
}

is_xcoff64() {
    # AIX od has no portable -N; use Python to read the XCOFF magic (0x01F7).
    "$PYTHONBIN" -c '
import sys
p = sys.argv[1]
with open(p, "rb") as fh:
    magic = fh.read(2)
sys.exit(0 if magic == b"\x01\xf7" else 1)
' "$1" 2>/dev/null
}

# Newest GCC runtime first (13 before 10). Unmatched globs are skipped by [ -e ].
GCC_LIBGCC_S=""
for src in /opt/freeware/lib/gcc/*/*/libgcc_s.a /opt/freeware/lib64/gcc/*/*/libgcc_s.a; do
    if [ -e "$src" ]; then
        GCC_LIBGCC_S="$src $GCC_LIBGCC_S"
    fi
done

# Always rebuild a loadable 64-bit archive with the exact member name ldd wants.
# Copying Toolbox stubs and ar r into them leaves an import file the loader cannot use.
rebuild_shared_archive() {
    dest=$1
    need=$2
    alts=$3
    shift 3

    tmpdir=/tmp/ncpa-ar-rebuild.$$
    rm -rf "$tmpdir"
    mkdir -p "$tmpdir"

    for src in "$@"; do
        [ -e "$src" ] || continue
        members=$(aix_ar_t "$src")
        echo "  Candidate $src members: $(echo "$members" | tr '\n' ' ')"
        pick=""
        for cand in $need $alts; do
            if echo "$members" | grep -qx "$cand"; then
                pick=$cand
                break
            fi
        done
        if [ -z "$pick" ]; then
            echo "  No matching member ($need / $alts) in $src"
            continue
        fi

        echo "  Extracting $src($pick) -> $dest($need)"
        if (
            cd "$tmpdir" || exit 1
            rm -f ./* 2>/dev/null || true
            ar -X64 x "$src" "$pick"
            if [ ! -f "$pick" ]; then
                echo "ERROR: ar -X64 x $src $pick did not produce a file"
                exit 1
            fi
            if [ "$pick" != "$need" ]; then
                cp "$pick" "$need"
            fi
            if ! is_xcoff64 "$need"; then
                echo "  Skipping $src($pick): not 64-bit XCOFF magic 0x01F7"
                exit 1
            fi
            aix_ar_create "$dest" "$need"
        ); then
            :
        else
            continue
        fi

        if aix_ar_t "$dest" | grep -qx "$need"; then
            echo "  Rebuilt $dest with 64-bit member $need from $src($pick)"
            rm -rf "$tmpdir"
            return 0
        fi
        echo "  WARNING: rebuilt $dest but member $need not listed"
    done

    rm -rf "$tmpdir"
    echo "ERROR: could not rebuild $dest with 64-bit member $need"
    echo "Looked at: $*"
    return 1
}

echo "***** aix/fix_libpath.sh - rebuilding loadable libgcc_s.a and libiconv.a"
rebuild_shared_archive "$NCPA_ROOT/lib/libgcc_s.a" "shr.o" "libgcc_s.so.1 libgcc_s.so shr_64.o" \
    $GCC_LIBGCC_S \
    /opt/freeware/lib64/libgcc_s.a \
    /opt/freeware/lib/libgcc_s.a \
    "$NCPA_ROOT/lib/libgcc_s.a" || exit 1

rebuild_shared_archive "$NCPA_ROOT/lib/libiconv.a" "libiconv.so.2" "libiconv.so.1 libiconv.so" \
    /opt/freeware/lib64/libiconv.a \
    /opt/freeware/lib/libiconv.a \
    "$NCPA_ROOT/lib/libiconv.a" || exit 1

# AIX ksh93/ldd load libiconv.a(shr4_64.o) from the first LIBPATH hit.
# GNU Toolbox libiconv does not have that member, so prepend /usr/lib members.
merge_ibm_libiconv_members() {
    dest=$1
    ibm=/usr/lib/libiconv.a
    if [ ! -e "$ibm" ]; then
        echo "  NOTE: $ibm not present; not merging IBM libiconv members"
        return 0
    fi
    tmpdir=/tmp/ncpa-iconv-ibm.$$
    rm -rf "$tmpdir"
    mkdir -p "$tmpdir"
    echo "  Merging 64-bit members from $ibm into $dest"
    (
        cd "$tmpdir" || exit 1
        for m in $(ar -X64 t "$ibm" 2>/dev/null); do
            [ -n "$m" ] || continue
            if [ "$m" = "libiconv.so.2" ] || [ "$m" = "libiconv.so.1" ]; then
                continue
            fi
            ar -X64 x "$ibm" "$m"
            ar -X64 r "$dest" "$m"
        done
        ar -X64 s "$dest" 2>/dev/null || true
    )
    echo "  libiconv.a members now: $(aix_ar_t "$dest" | tr '\n' ' ')"
    rm -rf "$tmpdir"
}

merge_ibm_libiconv_members "$NCPA_ROOT/lib/libiconv.a"

echo "***** aix/fix_libpath.sh - rewriting XCOFF loader imports"
$PYTHONBIN "$FIX_PY" --libpath "$TARGET_LIBPATH" --fail-on-freeware "$NCPA_ROOT/ncpa"

# Do not extract/re-ar libgcc_s.a or libiconv.a. Re-inserting those members
# makes the loader report "Cannot find ... (shr.o)" / "(libiconv.so.2)".
# libintl.a is what still absolute-imports freeware libiconv.
patch_archive_xcoff_members() {
    archive=$1
    tmpdir=/tmp/ncpa-xcoff-mem.$$
    rm -rf "$tmpdir"
    mkdir -p "$tmpdir"
    echo "  Patching 64-bit members in $archive"
    (
        cd "$tmpdir" || exit 1
        for m in $(ar -X64 t "$archive" 2>/dev/null); do
            [ -n "$m" ] || continue
            ar -X64 x "$archive" "$m"
            if [ ! -f "$m" ]; then
                continue
            fi
            before=$("$PYTHONBIN" -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$m")
            $PYTHONBIN "$FIX_PY" --libpath "$TARGET_LIBPATH" "$m"
            after=$("$PYTHONBIN" -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$m")
            if [ "$before" != "$after" ]; then
                echo "    updated member $m"
                ar -X64 r "$archive" "$m"
            fi
        done
        ar -X64 s "$archive" 2>/dev/null || true
    )
    rm -rf "$tmpdir"
}

if [ -f "$NCPA_ROOT/lib/libintl.a" ]; then
    patch_archive_xcoff_members "$NCPA_ROOT/lib/libintl.a" || exit 1
fi
if [ -f "$NCPA_ROOT/lib/libpython3.12.a" ]; then
    patch_archive_xcoff_members "$NCPA_ROOT/lib/libpython3.12.a" || exit 1
fi

echo "***** aix/fix_libpath.sh - archive member check"
echo "  libgcc_s.a members: $(aix_ar_t "$NCPA_ROOT/lib/libgcc_s.a" | tr '\n' ' ')"
echo "  libiconv.a members: $(aix_ar_t "$NCPA_ROOT/lib/libiconv.a" | tr '\n' ' ')"
if ! aix_ar_t "$NCPA_ROOT/lib/libgcc_s.a" | grep -qx 'shr.o'; then
    echo "ERROR: rebuilt libgcc_s.a is missing shr.o"
    exit 1
fi
if ! aix_ar_t "$NCPA_ROOT/lib/libiconv.a" | grep -qx 'libiconv.so.2'; then
    echo "ERROR: rebuilt libiconv.a is missing libiconv.so.2"
    exit 1
fi

echo "***** aix/fix_libpath.sh - verifying ncpa loader imports (if dump available)"
if command -v dump >/dev/null 2>&1; then
    hits=$(dump -X64 -H "$NCPA_ROOT/ncpa" 2>/dev/null | grep '/opt/freeware/' || true)
    if [ -n "$hits" ]; then
        echo "  NOTE: dump -X64 -H still mentions /opt/freeware in ncpa:"
        echo "$hits" | sed 's/^/    /'
    fi
else
    echo "  dump not available; skipped dump -X64 -H verification"
fi

echo "***** aix/fix_libpath.sh - completed successfully"
echo "Standalone check after install (do not export LIBPATH in your shell):"
echo "  ldd /usr/local/ncpa/ncpa"
echo "  ar -X64 t /usr/local/ncpa/lib/libgcc_s.a"
echo "  ar -X64 t /usr/local/ncpa/lib/libiconv.a"
echo "  startsrc -s ncpa"