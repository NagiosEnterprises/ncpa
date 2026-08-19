#!/usr/bin/env python3
"""Rewrite AIX XCOFF *loader* import paths for standalone NCPA installs.

Only the loader import string table is modified. Blind search-and-replace of
/opt/freeware across the whole file corrupts code and causes SIGILL.
"""

from __future__ import annotations

import argparse
import os
import struct
import sys
from typing import List, Optional, Tuple


FREEWARE_PREFIX = b"/opt/freeware/"
NCPA_LIB = b"/usr/local/ncpa/lib"
DEFAULT_LIBPATH = b"/usr/local/ncpa/lib:/usr/lib:/lib"
XCOFF32_MAGIC = 0x01DF
XCOFF64_MAGIC = 0x01F7


def read_cstring(data: bytes, offset: int) -> Tuple[bytes, int]:
    end = data.find(b"\0", offset)
    if end < 0:
        raise ValueError(f"Unterminated C string at offset {offset}")
    return data[offset:end], end + 1


def get_loader_import_table(data: bytes) -> Optional[Tuple[int, int]]:
    """Return (offset, length) of the XCOFF loader import string table."""
    if len(data) < 24:
        return None

    magic = struct.unpack(">H", data[0:2])[0]
    if magic == XCOFF32_MAGIC:
        f_opthdr = struct.unpack(">H", data[16:18])[0]
        file_hdr_size = 20
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
        aux_snloader_off = 50
        scnhdr_size = 72
        scnptr_off = 24
        scnptr_fmt = ">Q"
        ldr_hdr_size = 56
        l_istlen_off = 12
        l_impoff_off = 24
        l_impoff_fmt = ">Q"
    else:
        return None

    if f_opthdr < aux_snloader_off + 2:
        return None

    aux_off = file_hdr_size
    snloader = struct.unpack(
        ">H", data[aux_off + aux_snloader_off:aux_off + aux_snloader_off + 2]
    )[0]
    if snloader <= 0:
        return None

    scn_off = file_hdr_size + f_opthdr + (snloader - 1) * scnhdr_size
    scnptr_size = 4 if scnptr_fmt == ">I" else 8
    if scn_off + scnptr_off + scnptr_size > len(data):
        return None

    s_scnptr = struct.unpack(
        scnptr_fmt, data[scn_off + scnptr_off:scn_off + scnptr_off + scnptr_size]
    )[0]

    ldr_off = s_scnptr
    if ldr_off + ldr_hdr_size > len(data):
        return None

    l_istlen = struct.unpack(">I", data[ldr_off + l_istlen_off:ldr_off + l_istlen_off + 4])[0]
    impoff_size = 4 if l_impoff_fmt == ">I" else 8
    l_impoff = struct.unpack(
        l_impoff_fmt, data[ldr_off + l_impoff_off:ldr_off + l_impoff_off + impoff_size]
    )[0]

    imp_off = ldr_off + l_impoff
    if imp_off + l_istlen > len(data) or l_istlen <= 0:
        return None
    return imp_off, l_istlen


def rewrite_loader_imports(data: bytearray, new_libpath: bytes) -> Tuple[int, bool]:
    """Clear /opt/freeware import paths and update default LIBPATH.

    Returns (cleared_import_count, libpath_updated).
    """
    loc = get_loader_import_table(bytes(data))
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
            path, pos = read_cstring(bytes(data), pos)
            base, pos = read_cstring(bytes(data), pos)
            member, pos = read_cstring(bytes(data), pos)
        except ValueError:
            break
        entry_end = pos
        if entry_end > table_end:
            break

        if first:
            first = False
            if path and len(new_libpath) <= len(path):
                padded = new_libpath + (b":" * (len(path) - len(new_libpath)))
                data[start:start + len(path)] = padded
                libpath_updated = True
            continue

        if not path.startswith(FREEWARE_PREFIX):
            continue

        new_path = NCPA_LIB if len(NCPA_LIB) <= len(path) else b""
        new_entry = new_path + b"\0" + base + b"\0" + member + b"\0"
        old_len = entry_end - start
        if len(new_entry) > old_len:
            new_entry = b"\0" + base + b"\0" + member + b"\0"
        if len(new_entry) <= old_len:
            data[start:entry_end] = new_entry + (b"\0" * (old_len - len(new_entry)))
            cleared += 1

    return cleared, libpath_updated


def loader_freeware_imports(data: bytes) -> List[str]:
    loc = get_loader_import_table(data)
    if not loc:
        return []

    imp_off, istlen = loc
    table_end = imp_off + istlen
    pos = imp_off
    first = True
    found = []
    while pos < table_end:
        try:
            path, pos = read_cstring(data, pos)
            base, pos = read_cstring(data, pos)
            member, pos = read_cstring(data, pos)
        except ValueError:
            break
        if first:
            first = False
            continue
        if path.startswith(FREEWARE_PREFIX) and base:
            label = f"{path.decode('ascii', 'replace')}/{base.decode('ascii', 'replace')}"
            if member:
                label += f"({member.decode('ascii', 'replace')})"
            found.append(label)
    return found


def process_file(path: str, new_libpath: bytes) -> Tuple[int, bool, str]:
    with open(path, "rb") as fh:
        raw = fh.read()

    if len(raw) < 2:
        return 0, False, "skipped (too small)"

    magic = struct.unpack(">H", raw[0:2])[0]
    if magic not in (XCOFF32_MAGIC, XCOFF64_MAGIC):
        return 0, False, "skipped (not standalone XCOFF; archives are patched per-member)"

    data = bytearray(raw)
    cleared, libpath_updated = rewrite_loader_imports(data, new_libpath)

    if data != raw:
        with open(path, "wb") as fh:
            fh.write(data)

    return cleared, libpath_updated, "patched"


def remaining_freeware_imports(path: str) -> List[str]:
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) < 2 or struct.unpack(">H", data[0:2])[0] not in (
        XCOFF32_MAGIC,
        XCOFF64_MAGIC,
    ):
        return []
    return loader_freeware_imports(data)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="XCOFF binaries (not AIX .a archives)")
    parser.add_argument(
        "--libpath",
        default=DEFAULT_LIBPATH.decode(),
        help="Embedded LIBPATH to write when space allows",
    )
    parser.add_argument(
        "--fail-on-freeware",
        action="store_true",
        help="Exit non-zero if loader import paths still use /opt/freeware",
    )
    args = parser.parse_args(argv)
    new_libpath = args.libpath.encode("ascii")

    total_cleared = 0
    for path in args.paths:
        if not os.path.exists(path):
            print(f"ERROR: {path} does not exist", file=sys.stderr)
            return 1
        cleared, libpath_updated, status = process_file(path, new_libpath)
        total_cleared += cleared
        extra = ", updated embedded libpath" if libpath_updated else ""
        print(f"{path}: {status}; cleared {cleared} freeware loader import(s){extra}")

        leftovers = remaining_freeware_imports(path)
        if leftovers:
            print(f"  remaining freeware loader imports: {', '.join(leftovers)}", file=sys.stderr)
            if args.fail_on_freeware:
                return 1

    print(f"Total freeware loader imports cleared: {total_cleared}")
    return 0


if __name__ == "__main__":
    sys.exit(main())