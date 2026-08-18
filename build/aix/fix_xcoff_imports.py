#!/usr/bin/env python3
"""Rewrite AIX XCOFF loader import paths for standalone NCPA installs.

Absolute import IDs under /opt/freeware bypass LIBPATH at runtime. This tool:
1. Clears /opt/freeware import path components (basename + member remain)
2. Rewrites the embedded default libpath (first import ID) when present
"""

from __future__ import annotations

import argparse
import os
import struct
import sys
from typing import List, Optional, Tuple


FREEWARE_PREFIX = b"/opt/freeware/"
FREEWARE_LIB64 = b"/opt/freeware/lib64"
NCPA_LIB = b"/usr/local/ncpa/lib"
DEFAULT_LIBPATH = b"/usr/local/ncpa/lib:/usr/lib:/lib"
XCOFF32_MAGIC = 0x01DF
XCOFF64_MAGIC = 0x01F7

assert len(FREEWARE_LIB64) == len(NCPA_LIB)


def read_cstring(data: bytes, offset: int) -> Tuple[bytes, int]:
    end = data.find(b"\0", offset)
    if end < 0:
        raise ValueError(f"Unterminated C string at offset {offset}")
    return data[offset:end], end + 1


def rewrite_equal_length_lib64_paths(data: bytearray) -> int:
    """Map /opt/freeware/lib64 -> /usr/local/ncpa/lib (same length).

    Only rewrite when the path component ends at this boundary (NUL or ':'),
    so longer paths like /opt/freeware/lib64/gcc/... are left for clearing.
    """
    replaced = 0
    search_from = 0
    while True:
        idx = data.find(FREEWARE_LIB64, search_from)
        if idx < 0:
            break
        end = idx + len(FREEWARE_LIB64)
        if end < len(data) and data[end] in (0, ord(":")):
            data[idx:end] = NCPA_LIB
            replaced += 1
            search_from = end
        else:
            search_from = idx + 1
    return replaced


def clear_freeware_import_paths(data: bytearray) -> int:
    """Clear absolute /opt/freeware import path components in-place."""
    cleared = 0
    search_from = 0

    while True:
        idx = data.find(FREEWARE_PREFIX, search_from)
        if idx < 0:
            break

        try:
            path, after_path = read_cstring(bytes(data), idx)
            base, after_base = read_cstring(bytes(data), after_path)
            member, after_member = read_cstring(bytes(data), after_base)
        except ValueError:
            search_from = idx + 1
            continue

        # Import IDs have a basename. The embedded LIBPATH entry has empty base/member.
        if not base:
            search_from = idx + 1
            continue

        old_len = after_member - idx
        new_entry = b"\0" + base + b"\0" + member + b"\0"
        if len(new_entry) > old_len:
            raise RuntimeError(
                f"Cannot clear import path {path!r}: rewritten entry is longer "
                f"({len(new_entry)} > {old_len})"
            )

        padded = new_entry + (b"\0" * (old_len - len(new_entry)))
        data[idx:after_member] = padded
        cleared += 1
        search_from = idx + old_len

    return cleared


def update_embedded_libpath(data: bytearray, new_libpath: bytes) -> bool:
    """Update the first loader import ID (default LIBPATH) when XCOFF is parseable."""
    if len(data) < 24:
        return False

    magic = struct.unpack(">H", data[0:2])[0]
    if magic == XCOFF32_MAGIC:
        f_opthdr = struct.unpack(">H", data[16:18])[0]
        file_hdr_size = 20
        # o_snloader offset inside 32-bit auxiliary header
        aux_snloader_off = 50
        scnhdr_size = 40
        scnptr_off = 12
        scnptr_fmt = ">I"
        ldr_hdr_size = 32
        l_istlen_off = 12
        l_impoff_off = 20
        l_impoff_fmt = ">I"
    elif magic == XCOFF64_MAGIC:
        f_opthdr = struct.unpack(">H", data[16:18])[0]
        file_hdr_size = 24
        # o_snloader offset inside 64-bit auxiliary header
        aux_snloader_off = 50
        scnhdr_size = 72
        scnptr_off = 24
        scnptr_fmt = ">Q"
        ldr_hdr_size = 56
        l_istlen_off = 12
        l_impoff_off = 24
        l_impoff_fmt = ">Q"
    else:
        return False

    if f_opthdr < aux_snloader_off + 2:
        return False

    aux_off = file_hdr_size
    snloader = struct.unpack(
        ">H", data[aux_off + aux_snloader_off:aux_off + aux_snloader_off + 2]
    )[0]
    if snloader <= 0:
        return False

    scn_off = file_hdr_size + f_opthdr + (snloader - 1) * scnhdr_size
    scnptr_size = 4 if scnptr_fmt == ">I" else 8
    if scn_off + scnptr_off + scnptr_size > len(data):
        return False

    s_scnptr = struct.unpack(
        scnptr_fmt, data[scn_off + scnptr_off:scn_off + scnptr_off + scnptr_size]
    )[0]

    ldr_off = s_scnptr
    if ldr_off + ldr_hdr_size > len(data):
        return False

    l_istlen = struct.unpack(">I", data[ldr_off + l_istlen_off:ldr_off + l_istlen_off + 4])[0]
    impoff_size = 4 if l_impoff_fmt == ">I" else 8
    l_impoff = struct.unpack(
        l_impoff_fmt, data[ldr_off + l_impoff_off:ldr_off + l_impoff_off + impoff_size]
    )[0]

    imp_off = ldr_off + l_impoff
    if imp_off + l_istlen > len(data) or l_istlen <= 0:
        return False

    old_libpath, _ = read_cstring(bytes(data), imp_off)
    if not old_libpath:
        return False

    if len(new_libpath) > len(old_libpath):
        # Keep existing libpath if we cannot fit; import-path clearing plus
        # runtime LIBPATH still make installs standalone.
        return False

    padded = new_libpath + (b":" * (len(old_libpath) - len(new_libpath)))
    data[imp_off:imp_off + len(old_libpath)] = padded
    return True


def process_file(path: str, new_libpath: bytes) -> Tuple[int, int, bool]:
    with open(path, "rb") as fh:
        raw = fh.read()

    data = bytearray(raw)

    # Archives are rewritten in-place; import IDs are plain strings inside
    # member loader sections.
    rewritten_lib64 = rewrite_equal_length_lib64_paths(data)
    cleared = clear_freeware_import_paths(data)
    libpath_updated = update_embedded_libpath(data, new_libpath)

    if data != raw:
        with open(path, "wb") as fh:
            fh.write(data)

    return rewritten_lib64, cleared, libpath_updated


def remaining_freeware_imports(path: str) -> List[str]:
    with open(path, "rb") as fh:
        data = fh.read()

    found = []
    search_from = 0
    while True:
        idx = data.find(FREEWARE_PREFIX, search_from)
        if idx < 0:
            break
        try:
            path_comp, after_path = read_cstring(data, idx)
            base, after_base = read_cstring(data, after_path)
            member, after_member = read_cstring(data, after_base)
        except ValueError:
            search_from = idx + 1
            continue
        if base:
            member_s = member.decode("ascii", "replace")
            label = f"{path_comp.decode('ascii', 'replace')}/{base.decode('ascii', 'replace')}"
            if member_s:
                label += f"({member_s})"
            found.append(label)
            search_from = after_member
        else:
            search_from = idx + 1
    return found


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="XCOFF binaries or AIX .a archives")
    parser.add_argument(
        "--libpath",
        default=DEFAULT_LIBPATH.decode(),
        help="Embedded LIBPATH to write when space allows",
    )
    parser.add_argument(
        "--fail-on-freeware",
        action="store_true",
        help="Exit non-zero if any /opt/freeware import paths remain",
    )
    args = parser.parse_args(argv)
    new_libpath = args.libpath.encode("ascii")

    total_lib64 = 0
    total_cleared = 0
    for path in args.paths:
        if not os.path.exists(path):
            print(f"ERROR: {path} does not exist", file=sys.stderr)
            return 1
        rewritten_lib64, cleared, libpath_updated = process_file(path, new_libpath)
        total_lib64 += rewritten_lib64
        total_cleared += cleared
        status = (
            f"rewrote {rewritten_lib64} lib64 path(s), "
            f"cleared {cleared} freeware import path(s)"
        )
        if libpath_updated:
            status += ", updated embedded libpath"
        print(f"{path}: {status}")

        leftovers = remaining_freeware_imports(path)
        if leftovers:
            print(f"  remaining freeware imports: {', '.join(leftovers)}", file=sys.stderr)
            if args.fail_on_freeware:
                return 1

    print(
        f"Total lib64 paths rewritten: {total_lib64}; "
        f"freeware import paths cleared: {total_cleared}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())