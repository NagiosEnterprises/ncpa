#!/usr/bin/env python3
"""Rewrite AIX XCOFF *loader* import paths for standalone NCPA installs.

Only loader import C strings are modified, and only with same-length
replacements. Shortening a path and padding the triplet with extra NULs
creates empty import IDs; ldd then prints dspmsg 1312-042 and "Cannot find"
with a blank name.

Archives are patched in place (member bytes spliced back). Re-inserting a
shared member with `ar r` can make the loader report it missing.
"""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import subprocess
import sys
import tempfile
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


def pad_same_length(new: bytes, old: bytes, fill: bytes) -> Optional[bytes]:
    if len(new) > len(old):
        return None
    pad = len(old) - len(new)
    return new + (fill * pad)


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


def rewrite_loader_imports(data: bytearray, new_libpath: bytes) -> Tuple[int, bool]:
    """Rewrite freeware import paths in place without moving later strings.

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
        if pos > table_end:
            break

        if first:
            first = False
            if FREEWARE_PREFIX in path or path.startswith(b"/opt/freeware"):
                padded = pad_same_length(new_libpath, path, b":")
                if padded is not None:
                    data[start:start + len(path)] = padded
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


def remaining_freeware_imports(data: bytes) -> List[str]:
    found = []
    for i, (path, base, member) in enumerate(iter_import_ids(data)):
        if i == 0:
            continue
        if path.startswith(FREEWARE_PREFIX) and base:
            label = f"{path.decode('ascii', 'replace')}/{base.decode('ascii', 'replace')}"
            if member:
                label += f"({member.decode('ascii', 'replace')})"
            found.append(label)
    return found


def process_xcoff_bytes(raw: bytes, new_libpath: bytes) -> Tuple[bytes, int, bool, str]:
    if len(raw) < 2:
        return raw, 0, False, "skipped (too small)"
    magic = struct.unpack(">H", raw[0:2])[0]
    if magic not in (XCOFF32_MAGIC, XCOFF64_MAGIC):
        return raw, 0, False, "skipped (not XCOFF)"

    if malformed_import_count(raw):
        return raw, 0, False, "ERROR: file already has empty loader import IDs"
    data = bytearray(raw)
    cleared, libpath_updated = rewrite_loader_imports(data, new_libpath)
    if len(data) != len(raw):
        return raw, 0, False, "ERROR: rewriter changed file size"
    if malformed_import_count(bytes(data)):
        return raw, 0, False, "ERROR: rewrite produced empty loader import IDs"
    if bytes(data) == raw:
        return raw, 0, False, "unchanged"
    return bytes(data), cleared, libpath_updated, "patched"


def process_file(path: str, new_libpath: bytes) -> Tuple[int, bool, str]:
    with open(path, "rb") as fh:
        raw = fh.read()
    patched, cleared, libpath_updated, status = process_xcoff_bytes(raw, new_libpath)
    if status.startswith("ERROR"):
        return 0, False, status
    if patched != raw:
        with open(path, "wb") as fh:
            fh.write(patched)
    return cleared, libpath_updated, status


def list_ar64_members(archive: str) -> List[str]:
    for cmd in (
        ["ar", "-X64", "t", archive],
        ["ar", "-X64", "-t", archive],
    ):
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        except Exception:
            continue
        members = []
        failed = False
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("ar:") or "0707-" in line or "Member name" in line:
                failed = True
                break
            members.append(line)
        if members and not failed:
            return members
    return []


def process_archive(path: str, new_libpath: bytes) -> Tuple[int, bool, str]:
    """Patch XCOFF members inside an AIX archive without `ar r`."""
    members = list_ar64_members(path)
    if not members:
        return 0, False, "skipped (no 64-bit archive members listed)"

    with open(path, "rb") as fh:
        blob = bytearray(fh.read())

    tmp = tempfile.mkdtemp(prefix="ncpa-xcoff-ar-")
    total_cleared = 0
    libpath_updated = False
    changed = False
    leftover = []
    try:
        for member in members:
            extracted = os.path.join(tmp, os.path.basename(member))
            try:
                subprocess.check_call(
                    ["ar", "-X64", "x", os.path.abspath(path), member],
                    cwd=tmp,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                continue
            if not os.path.isfile(extracted):
                alt = os.path.join(tmp, member)
                if os.path.isfile(alt):
                    extracted = alt
                else:
                    continue
            with open(extracted, "rb") as fh:
                original = fh.read()
            patched, cleared, lp_upd, status = process_xcoff_bytes(original, new_libpath)
            leftover.extend(
                f"{member}: {item}" for item in remaining_freeware_imports(patched)
            )
            if status.startswith("ERROR"):
                return 0, False, f"{status} in member {member}"
            if patched == original:
                continue
            start = 0
            found = 0
            while True:
                off = blob.find(original, start)
                if off < 0:
                    break
                blob[off:off + len(patched)] = patched
                found += 1
                start = off + 1
            if found == 0:
                return (
                    0,
                    False,
                    f"ERROR: member {member} not found as contiguous bytes in {path}",
                )
            changed = True
            total_cleared += cleared
            libpath_updated = libpath_updated or lp_upd
            print(f"  {path}({member}): {status}; cleared {cleared} freeware import path(s)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if changed:
        with open(path, "wb") as fh:
            fh.write(blob)

    if leftover:
        return total_cleared, libpath_updated, "patched with remaining freeware imports: " + ", ".join(leftover)
    return total_cleared, libpath_updated, "patched" if changed else "unchanged"


def process_path(path: str, new_libpath: bytes) -> Tuple[int, bool, str]:
    with open(path, "rb") as fh:
        magic = fh.read(8)
    if magic.startswith(b"\x01\xf7") or magic.startswith(b"\x01\xdf"):
        return process_file(path, new_libpath)
    if path.endswith(".a") or magic.startswith(b"<bigaf>") or magic.startswith(b"<aiaff>") or magic.startswith(b"!<arch>"):
        return process_archive(path, new_libpath)
    return process_file(path, new_libpath)


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
        help="Exit non-zero if loader import paths still use /opt/freeware",
    )
    args = parser.parse_args(argv)
    new_libpath = args.libpath.encode("ascii")

    total_cleared = 0
    for path in args.paths:
        if not os.path.exists(path):
            print(f"ERROR: {path} does not exist", file=sys.stderr)
            return 1
        cleared, libpath_updated, status = process_path(path, new_libpath)
        if status.startswith("ERROR"):
            print(f"{path}: {status}", file=sys.stderr)
            return 1
        total_cleared += cleared
        extra = ", updated embedded libpath" if libpath_updated else ""
        print(f"{path}: {status}; cleared {cleared} freeware loader import(s){extra}")

        if "remaining freeware imports" in status and args.fail_on_freeware:
            return 1

        if not path.endswith(".a"):
            with open(path, "rb") as fh:
                leftovers = remaining_freeware_imports(fh.read())
            if leftovers:
                print(
                    f"  remaining freeware loader imports: {', '.join(leftovers)}",
                    file=sys.stderr,
                )
                if args.fail_on_freeware:
                    return 1

    print(f"Total freeware loader imports cleared: {total_cleared}")
    return 0


if __name__ == "__main__":
    sys.exit(main())