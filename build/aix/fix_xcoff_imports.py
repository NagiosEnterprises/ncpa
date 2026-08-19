#!/usr/bin/env python3
"""Rewrite AIX XCOFF *loader* import paths for standalone NCPA installs.

Only C strings are modified, and only with same-length replacements.
Shortening a path and padding with extra NULs creates empty import IDs;
ldd then prints dspmsg 1312-042 and "Cannot find" with a blank name.

Toolbox directories are matched as complete C strings:
  /opt/freeware/lib   -> /usr/local/ncpa/lib/
  /opt/freeware/lib64 -> /usr/local/ncpa/lib///
LIBPATH strings that search those dirs are colon-padded to the NCPA libpath.
Include paths and GCC BUILD LIBPATHs are left alone.

Works on standalone XCOFF and on AIX .a archives without extracting members.
"""

from __future__ import annotations

import argparse
import os
import struct
import sys
from typing import List, Optional, Tuple


FREEWARE_PREFIX = b"/opt/freeware/"
FREEWARE_LIB = b"/opt/freeware/lib"
FREEWARE_LIB64 = b"/opt/freeware/lib64"
NCPA_LIB = b"/usr/local/ncpa/lib"
DEFAULT_LIBPATH = b"/usr/local/ncpa/lib:/usr/lib:/lib"
XCOFF32_MAGIC = 0x01DF
XCOFF64_MAGIC = 0x01F7
# Ignore unterminated / huge matches so we do not pad megabytes of colons.
MAX_IMPORT_CSTRING = 1024


def read_cstring(data: bytes, offset: int) -> Tuple[bytes, int]:
    end = data.find(b"\0", offset)
    if end < 0:
        raise ValueError(f"Unterminated C string at offset {offset}")
    return data[offset:end], end + 1


def pad_same_length(new: bytes, old: bytes, fill: bytes) -> Optional[bytes]:
    if len(new) > len(old):
        return None
    pad = len(old) - len(new)
    return new + (fill * pad)


STYP_LOADER = 0x1000


def get_loader_import_table(data: bytes, base: int = 0) -> Optional[Tuple[int, int]]:
    """Return (offset, length) of the XCOFF loader import string table.

    Offsets are relative to the start of *data*. *base* is the start of the
    XCOFF object (0 for a standalone file, member offset inside an archive).
    Loader section is found by STYP_LOADER.
    """
    if base + 24 > len(data):
        return None

    magic = struct.unpack(">H", data[base:base + 2])[0]
    if magic == XCOFF32_MAGIC:
        file_hdr_size = 20
        scnhdr_size = 40
        scnptr_off = 20
        flags_off = 36
        scnptr_fmt = ">I"
        ldr_hdr_size = 32
        l_istlen_off = 12
        l_impoff_off = 20
        l_impoff_fmt = ">I"
    elif magic == XCOFF64_MAGIC:
        file_hdr_size = 24
        scnhdr_size = 72
        scnptr_off = 32
        flags_off = 64
        scnptr_fmt = ">Q"
        ldr_hdr_size = 56
        l_istlen_off = 12
        l_impoff_off = 24
        l_impoff_fmt = ">Q"
    else:
        return None

    nscns = struct.unpack(">H", data[base + 2:base + 4])[0]
    f_opthdr = struct.unpack(">H", data[base + 16:base + 18])[0]
    if nscns <= 0 or nscns > 64 or f_opthdr > 512:
        return None

    scn_base = base + file_hdr_size + f_opthdr
    scnptr_size = 4 if scnptr_fmt == ">I" else 8
    ldr_off = None
    for i in range(nscns):
        off = scn_base + i * scnhdr_size
        if off + flags_off + 4 > len(data):
            return None
        flags = struct.unpack(">I", data[off + flags_off:off + flags_off + 4])[0]
        if (flags & STYP_LOADER) == 0:
            continue
        scnptr = struct.unpack(
            scnptr_fmt, data[off + scnptr_off:off + scnptr_off + scnptr_size]
        )[0]
        ldr_off = base + scnptr
        break

    if ldr_off is None or ldr_off <= base or ldr_off + ldr_hdr_size > len(data):
        return None

    l_istlen = struct.unpack(
        ">I", data[ldr_off + l_istlen_off:ldr_off + l_istlen_off + 4]
    )[0]
    impoff_size = 4 if l_impoff_fmt == ">I" else 8
    l_impoff = struct.unpack(
        l_impoff_fmt,
        data[ldr_off + l_impoff_off:ldr_off + l_impoff_off + impoff_size],
    )[0]

    imp_off = ldr_off + l_impoff
    if l_istlen < 8 or l_istlen > 65536 or imp_off + l_istlen > len(data):
        return None
    return imp_off, l_istlen


def iter_import_ids(data: bytes) -> List[Tuple[bytes, bytes, bytes]]:
    loc = get_loader_import_table(data)
    if not loc:
        return []
    imp_off, istlen = loc
    table_end = imp_off + istlen
    pos = imp_off
    ids = []
    while pos < table_end:
        try:
            path, pos = read_cstring(data, pos)
            base, pos = read_cstring(data, pos)
            member, pos = read_cstring(data, pos)
        except ValueError:
            break
        ids.append((path, base, member))
    return ids


def rewrite_loader_imports(data: bytearray, new_libpath: bytes, base: int = 0) -> Tuple[int, bool]:
    """Rewrite freeware import paths in place without moving later strings.

    Returns (cleared_import_count, libpath_updated). *base* is the XCOFF
    object start inside *data*.
    """
    loc = get_loader_import_table(data, base)
    if not loc:
        return 0, False

    imp_off, istlen = loc
    table_end = imp_off + istlen
    pos = imp_off
    first = True
    cleared = 0
    libpath_updated = False

    while pos < table_end:
        start = pos
        try:
            path, pos = read_cstring(data, pos)
            libbase, pos = read_cstring(data, pos)
            member, pos = read_cstring(data, pos)
        except ValueError:
            break
        if pos > table_end:
            break

        if first:
            first = False
            if FREEWARE_PREFIX in path or path.startswith(b"/opt/freeware"):
                replacement = rewrite_libpath_components(path)
                if replacement is None:
                    replacement = pad_same_length(new_libpath, path, b":")
                if replacement is not None:
                    data[start:start + len(path)] = replacement
                    libpath_updated = True
            continue

        if not path.startswith(FREEWARE_PREFIX):
            continue

        padded = pad_same_length(NCPA_LIB, path, b"/")
        if padded is None:
            print(
                f"  WARNING: cannot fit {NCPA_LIB.decode()} into import path "
                f"{path.decode('ascii', 'replace')!r} ({len(path)} bytes)",
                file=sys.stderr,
            )
            continue
        data[start:start + len(path)] = padded
        cleared += 1

    return cleared, libpath_updated


def rewrite_all_xcoff_loaders(data: bytearray, new_libpath: bytes) -> Tuple[int, bool]:
    """Rewrite loader import tables of every XCOFF object in a file or archive."""
    total = 0
    lp_any = False
    start = 0
    while start < len(data) - 2:
        idx64 = data.find(b"\x01\xf7", start)
        idx32 = data.find(b"\x01\xdf", start)
        found = [i for i in (idx64, idx32) if i >= 0]
        if not found:
            break
        idx = min(found)
        loc = get_loader_import_table(data, idx)
        if loc:
            cleared, lp = rewrite_loader_imports(data, new_libpath, idx)
            total += cleared
            lp_any = lp_any or lp
        start = idx + 2
    return total, lp_any


def is_toolbox_lib_dir(part: bytes) -> bool:
    return part in (FREEWARE_LIB, FREEWARE_LIB64) or part.startswith(
        FREEWARE_LIB + b"/"
    ) or part.startswith(FREEWARE_LIB64 + b"/")


def is_toolbox_lib_libpath(value: bytes) -> bool:
    """True for colon-separated search paths that include Toolbox lib dirs."""
    if b":" not in value:
        return False
    return any(is_toolbox_lib_dir(part) for part in value.split(b":"))


def rewrite_libpath_components(libpath: bytes) -> Optional[bytes]:
    """Replace Toolbox lib dir components in a LIBPATH, keeping total length."""
    parts = libpath.split(b":")
    new_parts = []
    changed = False
    for part in parts:
        if is_toolbox_lib_dir(part):
            padded = pad_same_length(NCPA_LIB, part, b"/")
            if padded is None:
                return None
            new_parts.append(padded)
            changed = True
        else:
            new_parts.append(part)
    if not changed:
        return None
    result = b":".join(new_parts)
    if len(result) != len(libpath):
        return None
    return result


def replace_dir_occurrences(data: bytearray, old: bytes, skip_next: Optional[int] = None) -> int:
    """Replace every occurrence of old with a same-length NCPA lib dir.

    skip_next avoids treating /opt/freeware/lib as the prefix of lib64.
    The following byte is left unchanged (NUL for import IDs, ':' for LIBPATH).
    """
    padded = pad_same_length(NCPA_LIB, old, b"/")
    if padded is None:
        return 0
    n = len(old)
    count = 0
    start = 0
    while True:
        idx = data.find(old, start)
        if idx < 0:
            return count
        after = idx + n
        nxt = data[after] if after < len(data) else None
        if skip_next is not None and nxt == skip_next:
            start = idx + 1
            continue
        data[idx:after] = padded
        count += 1
        start = after


def rewrite_exact_freeware_cstrings(data: bytearray, new_libpath: bytes) -> Tuple[int, int]:
    """Same-length rewrite of Toolbox lib dirs and LIBPATHs anywhere in a file."""
    del new_libpath
    # Longer name first. Skip next-byte '6' so 'lib' is not a prefix of 'lib64'.
    dirs = replace_dir_occurrences(data, FREEWARE_LIB64)
    dirs += replace_dir_occurrences(data, FREEWARE_LIB, skip_next=ord("6"))
    return dirs, 0


def remaining_absolute_freeware_dirs(data: bytes) -> List[str]:
    """Leftover /opt/freeware/lib or lib64 that is still an import path (next byte NUL)."""
    found = []
    for needle in (FREEWARE_LIB64, FREEWARE_LIB):
        n = len(needle)
        start = 0
        while True:
            idx = data.find(needle, start)
            if idx < 0:
                break
            after = idx + n
            nxt = data[after] if after < len(data) else None
            if needle == FREEWARE_LIB and nxt == ord("6"):
                start = idx + 1
                continue
            if nxt == 0:
                found.append(needle.decode("ascii"))
            start = idx + 1
    return found


def malformed_import_count(data: bytes) -> int:
    """Count import IDs that would make ldd print a blank 'Cannot find'."""
    ids = iter_import_ids(data)
    bad = 0
    for i, (path, base, member) in enumerate(ids):
        if i == 0:
            continue
        if not base or (not path and not base and not member):
            bad += 1
    return bad


def process_bytes(raw: bytes, new_libpath: bytes) -> Tuple[bytes, int, bool, str]:
    """Patch standalone XCOFF or an AIX archive; file size must not change."""
    if len(raw) < 2:
        return raw, 0, False, "skipped (too small)"

    data = bytearray(raw)
    dirs, libpaths = rewrite_exact_freeware_cstrings(data, new_libpath)
    extra, lp = rewrite_all_xcoff_loaders(data, new_libpath)
    cleared = dirs + libpaths + extra
    libpath_updated = libpaths > 0 or lp

    if len(data) != len(raw):
        return raw, 0, False, "ERROR: rewriter changed file size"

    leftover = remaining_absolute_freeware_dirs(bytes(data))
    if leftover:
        print(
            "  WARNING: leftover NUL-terminated Toolbox lib dirs: "
            + ", ".join(leftover),
            file=sys.stderr,
        )
    if bytes(data) == raw:
        return raw, 0, False, "unchanged"
    extra = ""
    if dirs:
        extra = f", rewrote {dirs} Toolbox lib dir(s)"
    return bytes(data), cleared, libpath_updated, "patched" + extra


def process_file(path: str, new_libpath: bytes) -> Tuple[int, bool, str]:
    with open(path, "rb") as fh:
        raw = fh.read()
    patched, cleared, libpath_updated, status = process_bytes(raw, new_libpath)
    if status.startswith("ERROR"):
        return 0, False, status
    if patched != raw:
        with open(path, "wb") as fh:
            fh.write(patched)
    return cleared, libpath_updated, status


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="XCOFF binaries, shared objects, or AIX .a archives")
    parser.add_argument(
        "--libpath",
        default=DEFAULT_LIBPATH.decode(),
        help="Embedded LIBPATH to write when space allows",
    )
    parser.add_argument(
        "--fail-on-freeware",
        action="store_true",
        help="Exit non-zero if absolute /opt/freeware/lib import dirs remain",
    )
    args = parser.parse_args(argv)
    new_libpath = args.libpath.encode("ascii")

    total_cleared = 0
    for path in args.paths:
        if not os.path.exists(path):
            print(f"ERROR: {path} does not exist", file=sys.stderr)
            return 1
        cleared, libpath_updated, status = process_file(path, new_libpath)
        if status.startswith("ERROR"):
            print(f"{path}: {status}", file=sys.stderr)
            return 1
        total_cleared += cleared
        extra = ", updated embedded libpath" if libpath_updated else ""
        print(f"{path}: {status}; cleared {cleared} freeware loader import(s){extra}")

        if "remaining freeware" in status and args.fail_on_freeware:
            print(
                f"ERROR: {path} still has absolute Toolbox lib import paths",
                file=sys.stderr,
            )
            return 1

    print(f"Total freeware loader imports cleared: {total_cleared}")
    return 0


if __name__ == "__main__":
    sys.exit(main())