#!/usr/bin/env python3
"""Rewrite AIX XCOFF *loader* import paths for standalone NCPA installs.

Only C strings are modified, and only with same-length replacements.
Shortening a path and padding with extra NULs creates empty import IDs;
ldd then prints dspmsg 1312-042 and "Cannot find" with a blank name.

/opt/freeware/lib is 17 bytes; /usr/local/ncpa/lib is 19. Those import
paths cannot be rewritten in place, so they are cleared (empty path =
LIBPATH search) and the loader import table is compacted. /opt/freeware/lib64
is 19 bytes and is rewritten in place to /usr/local/ncpa/lib.

AIX big archives are walked member-by-member. If dump still shows Toolbox
import IDs after an in-place rewrite, members are extracted with ar -X64,
patched, and spliced back (or replaced with ar -X64 r for libpython/libintl).
"""

from __future__ import annotations

import argparse
import os
import struct
import subprocess
import sys
import tempfile
from typing import Iterable, List, Optional, Tuple


FREEWARE_PREFIX = b"/opt/freeware/"
FREEWARE_LIB = b"/opt/freeware/lib"
FREEWARE_LIB64 = b"/opt/freeware/lib64"
NCPA_LIB = b"/usr/local/ncpa/lib"
DEFAULT_LIBPATH = b"/usr/local/ncpa/lib:/usr/lib:/lib"
XCOFF32_MAGIC = 0x01DF
XCOFF64_MAGIC = 0x01F7
# Older AIX 64-bit objects (infania/IBM filehdr docs).
XCOFF64_MAGIC_OLD = 0x01EF
BIGAF_MAGIC = b"<bigaf>\n"
# Ignore unterminated / huge matches so we do not pad megabytes of colons.
MAX_IMPORT_CSTRING = 1024
# Do not ar-replace GCC/GNU iconv members; that made them unloadable.
NO_AR_REPLACE = {"libgcc_s.a", "libiconv.a"}

# dump -H PATH / BASE / MEMBER triplets that still block standalone installs.
IMPORT_TRIPLETS = (
    (b"libintl.a", b"libintl.so.8"),
    (b"libiconv.a", b"libiconv.so.2"),
    (b"libpython3.12.a", b"libpython3.12.so"),
    (b"libgcc_s.a", b"shr.o"),
    (b"libffi.a", b"libffi.so.8"),
    (b"libz.a", b"libz.so.1"),
    (b"libsqlite3.a", b"libsqlite3.so.0"),
)


def read_cstring(data: bytes, offset: int) -> Tuple[bytes, int]:
    # Do not use bytes.find(b"\\0"): AIX Python treats NUL needles as C strings
    # and can match immediately, making every import ID look empty.
    end = offset
    while end < len(data) and data[end] != 0:
        end += 1
    if end >= len(data):
        raise ValueError(f"Unterminated C string at offset {offset}")
    return data[offset:end], end + 1


def pad_same_length(new: bytes, old: bytes, fill: bytes) -> Optional[bytes]:
    if len(new) > len(old):
        return None
    pad = len(old) - len(new)
    return new + (fill * pad)


def ascii_int(buf: bytes) -> int:
    text = buf.strip()
    if not text:
        return 0
    return int(text)


def hex_preview(data: bytes, limit: int = 64) -> str:
    shown = data[:limit]
    hexed = " ".join(f"{b:02x}" for b in shown)
    asciiish = "".join(chr(b) if 32 <= b < 127 else "." for b in shown)
    return f"{hexed}  {asciiish}"


STYP_LOADER = 0x1000


def get_loader_import_table(
    data: bytes, base: int = 0
) -> Optional[Tuple[int, int, int, int]]:
    """Return (imp_off, istlen, ldr_off, nimpid) for the loader import table.

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
        flags_size = 2
        scnptr_fmt = ">I"
        ldr_hdr_size = 32
        l_istlen_off = 12
        l_impoff_off = 20
        l_impoff_fmt = ">I"
    elif magic in (XCOFF64_MAGIC, XCOFF64_MAGIC_OLD):
        file_hdr_size = 24
        scnhdr_size = 72
        scnptr_off = 32
        flags_off = 64
        flags_size = 4
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
        if off + flags_off + flags_size > len(data):
            return None
        if flags_size == 2:
            flags = struct.unpack(">H", data[off + flags_off:off + flags_off + 2])[0]
        else:
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
    l_nimpid = struct.unpack(">I", data[ldr_off + 16:ldr_off + 20])[0]
    if l_nimpid <= 0 or l_nimpid > 512:
        l_nimpid = 0
    return imp_off, l_istlen, ldr_off, l_nimpid


def iter_xcoff_bases(data: bytes) -> Iterable[int]:
    start = 0
    magics = (b"\x01\xf7", b"\x01\xef", b"\x01\xdf")
    while start < len(data) - 2:
        found = [data.find(m, start) for m in magics]
        found = [i for i in found if i >= 0]
        if not found:
            return
        idx = min(found)
        yield idx
        start = idx + 2


def iter_import_ids(data: bytes, base: int = 0) -> List[Tuple[bytes, bytes, bytes]]:
    loc = get_loader_import_table(data, base)
    if not loc:
        return []
    imp_off, istlen, _ldr_off, nimpid = loc
    table_end = imp_off + istlen
    pos = imp_off
    ids = []
    while pos < table_end:
        if nimpid and len(ids) >= nimpid:
            break
        try:
            path, pos = read_cstring(data, pos)
            libbase, pos = read_cstring(data, pos)
            member, pos = read_cstring(data, pos)
        except ValueError:
            break
        ids.append((path, libbase, member))
    return ids


def normalize_import_path(path: bytes, new_libpath: bytes, is_libpath: bool) -> bytes:
    """Rewrite a stored import path. May shrink; never grows past new_libpath."""
    if is_libpath:
        parts = path.split(b":") if path else []
        out = []
        for part in parts:
            if is_toolbox_lib_dir(part):
                padded = pad_same_length(NCPA_LIB, part, b"/")
                if padded is not None:
                    out.append(NCPA_LIB)
                continue
            if part:
                out.append(part)
        return b":".join(out)

    if not path.startswith(FREEWARE_PREFIX) and path not in (FREEWARE_LIB, FREEWARE_LIB64):
        return path
    padded = pad_same_length(NCPA_LIB, path, b"/")
    if padded is not None:
        return padded
    # /opt/freeware/lib is 17 bytes; /usr/local/ncpa/lib is 19. Empty path
    # means the AIX loader searches LIBPATH (same as -bnoipath).
    return b""


def rewrite_loader_imports(data: bytearray, new_libpath: bytes, base: int = 0) -> Tuple[int, bool]:
    """Rebuild the loader import ID table, shrinking 17-byte freeware paths.

    Returns (cleared_import_count, libpath_updated). *base* is the XCOFF
    object start inside *data*.
    """
    loc = get_loader_import_table(data, base)
    if not loc:
        return 0, False

    imp_off, istlen, ldr_off, _nimpid = loc
    ids = iter_import_ids(data, base)
    if not ids:
        return 0, False

    new_ids = []
    cleared = 0
    libpath_updated = False
    for i, (path, libbase, member) in enumerate(ids):
        new_path = normalize_import_path(path, new_libpath, is_libpath=(i == 0))
        if i == 0:
            if new_path != path:
                libpath_updated = True
        elif new_path != path:
            cleared += 1
        new_ids.append((new_path, libbase, member))

    new_table = b"".join(
        p + b"\0" + libbase + b"\0" + member + b"\0"
        for p, libbase, member in new_ids
    )
    if len(new_table) > istlen:
        print(
            "  WARNING: rebuilt import table "
            f"({len(new_table)} bytes) does not fit in {istlen} bytes",
            file=sys.stderr,
        )
        return 0, False

    data[imp_off:imp_off + len(new_table)] = new_table
    if len(new_table) < istlen:
        data[imp_off + len(new_table):imp_off + istlen] = b"\0" * (istlen - len(new_table))
    struct.pack_into(">I", data, ldr_off + 12, len(new_table))
    return cleared, libpath_updated


def rewrite_all_xcoff_loaders(data: bytearray, new_libpath: bytes) -> Tuple[int, bool]:
    """Rewrite loader import tables of every XCOFF object in a blob."""
    total = 0
    lp_any = False
    for idx in iter_xcoff_bases(data):
        loc = get_loader_import_table(data, idx)
        if loc:
            cleared, lp = rewrite_loader_imports(data, new_libpath, idx)
            total += cleared
            lp_any = lp_any or lp
    return total, lp_any


def is_toolbox_lib_dir(part: bytes) -> bool:
    return part in (FREEWARE_LIB, FREEWARE_LIB64) or part.startswith(
        FREEWARE_LIB + b"/"
    ) or part.startswith(FREEWARE_LIB64 + b"/")


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


def replace_utf16_dir_occurrences(data: bytearray, old_ascii: bytes, skip_ascii_next: Optional[int] = None) -> int:
    """Same-length UTF-16LE/BE rewrite of a Toolbox lib dir."""
    count = 0
    new_ascii = NCPA_LIB
    if len(new_ascii) != len(old_ascii):
        return 0
    for enc in ("utf-16le", "utf-16be"):
        old = old_ascii.decode("ascii").encode(enc)
        new = new_ascii.decode("ascii").encode(enc)
        skip_next = None
        if skip_ascii_next is not None:
            skip_next = skip_ascii_next if enc == "utf-16be" else None
            # UTF-16LE: ASCII '6' is 0x36 followed by 0x00; check the first
            # extra byte of the next character.
        start = 0
        n = len(old)
        while True:
            idx = data.find(old, start)
            if idx < 0:
                break
            after = idx + n
            if skip_ascii_next is not None:
                if enc == "utf-16le":
                    nxt = data[after] if after < len(data) else None
                    if nxt == skip_ascii_next:
                        start = idx + 2
                        continue
                elif enc == "utf-16be":
                    nxt = data[after + 1] if after + 1 < len(data) else None
                    if nxt == skip_ascii_next:
                        start = idx + 2
                        continue
            data[idx:after] = new
            count += 1
            start = after
    return count


def rewrite_exact_freeware_cstrings(data: bytearray, new_libpath: bytes) -> Tuple[int, int]:
    """Same-length rewrite of Toolbox lib dirs anywhere in a blob."""
    del new_libpath
    dirs = replace_dir_occurrences(data, FREEWARE_LIB64)
    dirs += replace_dir_occurrences(data, FREEWARE_LIB, skip_next=ord("6"))
    dirs += replace_utf16_dir_occurrences(data, FREEWARE_LIB64)
    dirs += replace_utf16_dir_occurrences(data, FREEWARE_LIB, skip_ascii_next=ord("6"))
    return dirs, 0


def preceding_cstring(data: bytes, next_field: int) -> Tuple[int, bytes]:
    """Path C-string immediately before *next_field*, separated by a NUL.

    Import IDs are path\\0base\\0member\\0. *next_field* is the start of base,
    so the byte before it is the NUL that terminates path.
    """
    if next_field <= 0:
        return 0, b""
    if data[next_field - 1] != 0:
        return next_field, b""
    path_end = next_field - 1
    i = path_end - 1
    while i >= 0 and data[i] != 0:
        i -= 1
    start = i + 1
    return start, bytes(data[start:path_end])


def iter_base_member_offsets(data: bytes, base: bytes, member: bytes) -> Iterable[int]:
    """Yield start offsets of `base` in `base\\0member` without NUL find needles."""
    start = 0
    while True:
        idx = data.find(base, start)
        if idx < 0:
            return
        after = idx + len(base)
        if after < len(data) and data[after] == 0:
            mem_at = after + 1
            if data[mem_at:mem_at + len(member)] == member:
                mem_end = mem_at + len(member)
                if mem_end == len(data) or data[mem_end] == 0:
                    yield idx
        start = idx + 1


def freeware_dir_in_path(path: bytes, path_off: int) -> Optional[Tuple[int, bytes]]:
    """Return (offset, dir_bytes) if *path* is or ends with a Toolbox lib dir."""
    if path in (FREEWARE_LIB, FREEWARE_LIB64) or path.startswith(FREEWARE_PREFIX):
        return path_off, path
    for needle in (FREEWARE_LIB64, FREEWARE_LIB):
        if path.endswith(needle):
            return path_off + len(path) - len(needle), needle
    return None


def replace_known_import_triplets(data: bytearray) -> int:
    """Rewrite PATH in stored dump-style import IDs (path\\0base\\0member)."""
    count = 0
    for base, member in IMPORT_TRIPLETS:
        for idx in list(iter_base_member_offsets(data, base, member)):
            path_off, path = preceding_cstring(data, idx)
            span = freeware_dir_in_path(path, path_off)
            if span is None:
                continue
            dir_off, old_dir = span
            padded = pad_same_length(NCPA_LIB, old_dir, b"/")
            if padded is None:
                # 17-byte /opt/freeware/lib cannot hold a 19-byte NCPA path.
                # rewrite_loader_imports clears these and compacts the table.
                continue
            data[dir_off:dir_off + len(old_dir)] = padded
            count += 1
    return count


def stored_freeware_import_triplets(data: bytes) -> List[str]:
    """Import IDs that dump would print as /opt/freeware/lib + some .a member."""
    found = []
    for base, member in IMPORT_TRIPLETS:
        for idx in iter_base_member_offsets(data, base, member):
            path_off, path = preceding_cstring(data, idx)
            if freeware_dir_in_path(path, path_off) is None:
                continue
            found.append(
                f"{path.decode('ascii', 'replace')} {base.decode()} {member.decode()}"
            )
    return found


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


def diagnose_blob(data: bytes, label: str) -> None:
    ascii_off = data.find(FREEWARE_LIB)
    utf16le = data.find("/opt/freeware/lib".encode("utf-16le"))
    utf16be = data.find("/opt/freeware/lib".encode("utf-16be"))
    print(
        f"  {label}: size={len(data)} magic={hex_preview(data, 8)} "
        f"ascii_freeware={ascii_off} utf16le={utf16le} utf16be={utf16be}"
    )
    for base, member in IMPORT_TRIPLETS:
        hits = list(iter_base_member_offsets(data, base, member))
        if not hits:
            continue
        for idx in hits[:4]:
            path_off, path = preceding_cstring(data, idx)
            print(
                f"    import {path.decode('ascii', 'replace')!r} "
                f"{base.decode()} {member.decode()} @ {path_off}"
            )
            preview_at = max(0, path_off - 8)
            print(f"      bytes: {hex_preview(data[preview_at:idx + len(base) + 1], 80)}")
    ids = []
    for idx in iter_xcoff_bases(data):
        ids.extend(iter_import_ids(data, idx))
        if ids:
            break
    if ids:
        print(f"    parsed loader import IDs ({len(ids)}):")
        for i, (path, libbase, member) in enumerate(ids[:12]):
            print(
                f"      {i} {path.decode('ascii', 'replace')!r} "
                f"{libbase.decode('ascii', 'replace')} "
                f"{member.decode('ascii', 'replace')}"
            )


def iter_aix_bigaf_members(data: bytes) -> Iterable[Tuple[str, int, int]]:
    """Yield (name, data_offset, size) for AIX big-archive members."""
    if not data.startswith(BIGAF_MAGIC) or len(data) < 128:
        return
    first = ascii_int(data[68:88])
    last = ascii_int(data[88:108])
    if first <= 0:
        return
    seen = set()
    off = first
    for _ in range(256):
        if not off or off in seen or off + 114 > len(data):
            return
        seen.add(off)
        size = ascii_int(data[off:off + 20])
        nxt = ascii_int(data[off + 20:off + 40])
        namelen = ascii_int(data[off + 108:off + 112])
        if namelen < 0 or namelen > 1024 or size < 0:
            return
        name_padded = (namelen + 1) & ~1
        data_off = off + 112 + name_padded + 2
        name = data[off + 112:off + 112 + namelen].decode("ascii", "replace")
        if size > 0 and data_off + size <= len(data):
            yield name, data_off, size
        if off == last:
            return
        off = nxt


def process_xcoff_blob(data: bytearray, new_libpath: bytes) -> Tuple[int, bool]:
    dirs, _libpaths = rewrite_exact_freeware_cstrings(data, new_libpath)
    trips = replace_known_import_triplets(data)
    extra, lp = rewrite_all_xcoff_loaders(data, new_libpath)
    return dirs + trips + extra, lp


def process_bytes(raw: bytes, new_libpath: bytes) -> Tuple[bytes, int, bool, str]:
    """Patch standalone XCOFF or an AIX archive; file size must not change."""
    if len(raw) < 2:
        return raw, 0, False, "skipped (too small)"

    data = bytearray(raw)
    cleared = 0
    libpath_updated = False
    members = list(iter_aix_bigaf_members(raw))
    if members:
        for name, off, size in members:
            sl = bytearray(data[off:off + size])
            extra, lp = process_xcoff_blob(sl, new_libpath)
            data[off:off + size] = sl
            cleared += extra
            libpath_updated = libpath_updated or lp
            if extra:
                print(f"  archive member {name}: cleared {extra} freeware import(s)")
        # Member walk already rewrote XCOFF. Still do whole-file C-string
        # replaces for stubs that sit outside member bounds; skip loader
        # scans that can match 0x01F7 in archive headers.
        dirs, _libpaths = rewrite_exact_freeware_cstrings(data, new_libpath)
        trips = replace_known_import_triplets(data)
        cleared += dirs + trips
    else:
        extra, lp = process_xcoff_blob(data, new_libpath)
        cleared += extra
        libpath_updated = libpath_updated or lp

    if len(data) != len(raw):
        return raw, 0, False, "ERROR: rewriter changed file size"

    leftover = stored_freeware_import_triplets(bytes(data))
    if leftover:
        print(
            "  WARNING: stored Toolbox import IDs remain: " + "; ".join(leftover),
            file=sys.stderr,
        )
    if bytes(data) == raw:
        return raw, 0, False, "unchanged"
    extra = ""
    if cleared:
        extra = f", rewrote {cleared} Toolbox import(s)"
    return bytes(data), cleared, libpath_updated, "patched" + extra


def _ar_t64(archive_path: str) -> List[str]:
    env = os.environ.copy()
    env["OBJECT_MODE"] = "64"
    proc = subprocess.run(
        ["ar", "-X64", "t", archive_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if proc.returncode != 0:
        return []
    text = proc.stdout.decode("ascii", "replace")
    return [line.strip() for line in text.splitlines() if line.strip()]


def _ar_x64(archive_path: str, member: str, cwd: str) -> bool:
    env = os.environ.copy()
    env["OBJECT_MODE"] = "64"
    proc = subprocess.run(
        ["ar", "-X64", "x", os.path.abspath(archive_path), member],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    return proc.returncode == 0


def _ar_r64(archive_path: str, member_path: str) -> bool:
    env = os.environ.copy()
    env["OBJECT_MODE"] = "64"
    proc = subprocess.run(
        ["ar", "-X64", "r", os.path.abspath(archive_path), os.path.basename(member_path)],
        cwd=os.path.dirname(member_path) or ".",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if proc.returncode != 0:
        err = proc.stderr.decode("ascii", "replace").strip()
        print(f"  WARNING: ar -X64 r failed for {member_path}: {err}", file=sys.stderr)
        return False
    return True


def patch_via_ar_extract(path: str, new_libpath: bytes) -> Tuple[int, str]:
    """Extract 64-bit members, patch, splice back or ar-replace libpython/libintl."""
    if not path.endswith(".a"):
        return 0, "skipped (not an archive)"
    members = _ar_t64(path)
    if not members:
        return 0, "no 64-bit archive members"
    basename = os.path.basename(path)
    with open(path, "rb") as fh:
        blob = bytearray(fh.read())
    tmp = tempfile.mkdtemp(prefix="ncpa-xcoff-")
    cleared = 0
    changed = False
    try:
        for member in members:
            if member.startswith("__") or "/" in member:
                continue
            if not _ar_x64(path, member, tmp):
                continue
            mpath = os.path.join(tmp, member)
            if not os.path.isfile(mpath):
                continue
            with open(mpath, "rb") as fh:
                raw = fh.read()
            diagnose_blob(raw, f"extracted {basename}({member})")
            patched, extra, _lp, status = process_bytes(raw, new_libpath)
            print(f"    {member}: {status}")
            if patched == raw:
                continue
            off = blob.find(raw)
            if off >= 0 and len(patched) == len(raw):
                blob[off:off + len(raw)] = patched
                changed = True
                cleared += extra
                continue
            if basename in NO_AR_REPLACE:
                print(
                    f"  WARNING: cannot splice {member} into {basename}; "
                    "not using ar r on this archive",
                    file=sys.stderr,
                )
                continue
            with open(mpath, "wb") as fh:
                fh.write(patched)
            if _ar_r64(path, mpath):
                print(f"    replaced {basename}({member}) with ar -X64 r")
                with open(path, "rb") as fh:
                    blob[:] = fh.read()
                changed = True
                cleared += extra
    finally:
        try:
            for name in os.listdir(tmp):
                os.remove(os.path.join(tmp, name))
            os.rmdir(tmp)
        except OSError:
            pass

    if changed and blob:
        # ar r already wrote the archive; still persist splices.
        with open(path, "wb") as fh:
            fh.write(blob)
    return cleared, "extracted-member patch"


def process_file(path: str, new_libpath: bytes) -> Tuple[int, bool, str]:
    with open(path, "rb") as fh:
        raw = fh.read()
    diagnose_blob(raw, os.path.basename(path))
    patched, cleared, libpath_updated, status = process_bytes(raw, new_libpath)
    if status.startswith("ERROR"):
        return 0, False, status
    if patched != raw:
        with open(path, "wb") as fh:
            fh.write(patched)
        raw = patched

    leftover = stored_freeware_import_triplets(raw)
    if leftover:
        extra, _how = patch_via_ar_extract(path, new_libpath)
        cleared += extra
        with open(path, "rb") as fh:
            raw = fh.read()
        leftover = stored_freeware_import_triplets(raw)
        if extra and status == "unchanged":
            status = "patched via extracted members"
        elif extra:
            status += ", extracted-member patch"

    if leftover:
        status += "; remaining freeware imports: " + "; ".join(leftover)
    return cleared, libpath_updated, status


def verify_stored(paths: List[str]) -> int:
    failed = 0
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, "rb") as fh:
            data = fh.read()
        leftover = stored_freeware_import_triplets(data)
        if leftover:
            print(f"ERROR: stored Toolbox import IDs remain in {path}:")
            for line in leftover:
                print(f"    {line}")
            diagnose_blob(data, os.path.basename(path))
            failed = 1
        else:
            print(f"  {path}: no stored /opt/freeware import IDs for bundled .a members")
    return failed


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
    parser.add_argument(
        "--verify-stored",
        action="store_true",
        help="Only check for stored Toolbox import IDs; do not rewrite",
    )
    args = parser.parse_args(argv)
    new_libpath = args.libpath.encode("ascii")
    print(
        "Import path sizes: "
        f"/opt/freeware/lib={len(FREEWARE_LIB)} "
        f"/opt/freeware/lib64={len(FREEWARE_LIB64)} "
        f"/usr/local/ncpa/lib={len(NCPA_LIB)}"
    )

    if args.verify_stored:
        return verify_stored(args.paths)

    total_cleared = 0
    failed = 0
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
            failed = 1

    print(f"Total freeware loader imports cleared: {total_cleared}")
    return failed


if __name__ == "__main__":
    sys.exit(main())