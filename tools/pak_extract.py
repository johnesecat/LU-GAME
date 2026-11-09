#!/usr/bin/env python3
"""UE5 (pak v11) extractor for HDT-WindowsNoEditor.pak — correct encoded-entry format.

Encoded entry (v10+):
  u32 flags word:
    bits 0-5:   compression block size >> 11 (0x3F = u32 with real size follows)
    bits 6-21:  compression block count
    bit  22:    encrypted
    bits 23-28: compression slot (0 = none, n = footer name n-1)
    bit  29:    compressed size fits in u32 (else u64)
    bit  30:    uncompressed size fits in u32 (else u64)
    bit  31:    offset fits in u32 (else u64)
  then: [block size u32 if flags==0x3F], offset, uncompressed size, compressed size (if compressed),
        then u32 block sizes (only if >1 block or encrypted)
"""
import struct, sys, os, zlib, json

PAK = sys.argv[1] if len(sys.argv) > 1 else r"HDT\Content\Paks\HDT-WindowsNoEditor.pak"
OUT = sys.argv[2] if len(sys.argv) > 2 else "extracted"

f = open(PAK, "rb")
fsize = os.path.getsize(PAK)

# ---- footer ----
f.seek(fsize - 4096)
tail = f.read(4096)
magic_at = None
for i in range(len(tail) - 4):
    if tail[i:i+4] == b"\xE1\x12\x6F\x5A":
        magic_at = fsize - 4096 + i
        break
assert magic_at is not None
f.seek(magic_at)
footer = f.read(fsize - magic_at)
magic, version = struct.unpack_from("<II", footer, 0)
index_offset, index_size = struct.unpack_from("<qq", footer, 8)
print(f"pak v{version}, index at {index_offset} size {index_size}")

# ---- primary index ----
f.seek(index_offset)
idx = f.read(index_size)

def rd_i32(b, p): return struct.unpack_from("<i", b, p)[0], p+4
def rd_i64(b, p): return struct.unpack_from("<q", b, p)[0], p+8
def rd_fstr(b, p):
    n, p = rd_i32(b, p)
    s = b[p:p+n-1].decode("utf-8", "replace") if n > 0 else ""
    return s, p+n

p = 0
mount, p = rd_fstr(idx, p)
num_entries, p = rd_i32(idx, p)
path_hash_seed, p = rd_i64(idx, p)
has_phi, p = rd_i32(idx, p)
if has_phi:
    phi_off, p = rd_i64(idx, p)
    phi_size, p = rd_i64(idx, p)
    p += 20
has_fdi, p = rd_i32(idx, p)
if has_fdi:
    fdi_off, p = rd_i64(idx, p)
    fdi_size, p = rd_i64(idx, p)
    p += 20
enc_count, p = rd_i32(idx, p)
print(f"mount={mount} entries={num_entries} fdi={fdi_off}+{fdi_size} encCount={enc_count}")

# ---- full directory index ----
f.seek(fdi_off)
fdi = f.read(fdi_size)
q = 0
dir_count, q = rd_i32(fdi, q)
files = []
for d in range(dir_count):
    dirname, q = rd_fstr(fdi, q)
    file_count, q = rd_i32(fdi, q)
    for i in range(file_count):
        fname, q = rd_fstr(fdi, q)
        enc, q = rd_i32(fdi, q)
        files.append((dirname + "/" + fname, enc))
print(f"FDI files: {len(files)}")

# ---- decode encoded entries ----
def decode_entry(data, pos):
    flags, = struct.unpack_from("<I", data, pos)
    pos += 4
    # block size
    cbs = (flags & 0x3F) << 11
    if (flags & 0x3F) == 0x3F:
        cbs, = struct.unpack_from("<I", data, pos)
        pos += 4
    blocks = (flags >> 6) & 0xFFFF
    encrypted = (flags >> 22) & 1
    comp = (flags >> 23) & 0x3F
    size32 = (flags >> 29) & 1
    usize32 = (flags >> 30) & 1
    off32 = (flags >> 31) & 1
    # offset
    if off32:
        offset, = struct.unpack_from("<I", data, pos); pos += 4
    else:
        offset, = struct.unpack_from("<Q", data, pos); pos += 8
    # uncompressed size
    if usize32:
        usize, = struct.unpack_from("<I", data, pos); pos += 4
    else:
        usize, = struct.unpack_from("<Q", data, pos); pos += 8
    # compressed size (only if compressed)
    csize = usize
    if comp != 0:
        if size32:
            csize, = struct.unpack_from("<I", data, pos); pos += 4
        else:
            csize, = struct.unpack_from("<Q", data, pos); pos += 8
    # block sizes (only if >1 block or encrypted)
    block_sizes = []
    if blocks > 1 or (blocks == 1 and encrypted):
        for i in range(blocks):
            bs, = struct.unpack_from("<I", data, pos); pos += 4
            block_sizes.append(bs)
    return dict(offset=offset, usize=usize, csize=csize, comp=comp, blocks=blocks,
                encrypted=encrypted, cbs=cbs, block_sizes=block_sizes), pos

entries = {}
bad = 0
for name, enc in files:
    try:
        e, _ = decode_entry(idx, enc)
        entries[name] = e
    except Exception as ex:
        bad += 1
        entries[name] = dict(error=str(ex))
print(f"decoded {len(entries)-bad} entries, {bad} bad")

# sanity check first few
for name, e in list(entries.items())[:3]:
    print(name, {k: e.get(k) for k in ("offset","usize","csize","comp","blocks")})

# ---- extract ----
def read_entry(e):
    if e.get("error"):
        return None
    f.seek(e["offset"])
    if e["comp"] == 0:
        # uncompressed: data is csize bytes (== usize)
        return f.read(e["usize"])
    data = b""
    if e["blocks"] <= 1:
        raw = f.read(e["csize"])
        data = zlib.decompress(raw) if e["comp"] == 1 else raw
    else:
        # multi-block: blocks are contiguous after the entry header
        # block boundaries: each block is cbs bytes (last one smaller)
        remaining = e["csize"]
        produced = 0
        pos = e["offset"]
        for bs in (e["block_sizes"] or []):
            f.seek(pos)
            raw = f.read(bs)
            data += zlib.decompress(raw) if e["comp"] == 1 else raw
            pos += bs
    return data

count = 0
manifest = {}
for name, e in entries.items():
    out_path = os.path.join(OUT, name.replace("/", os.sep))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    try:
        data = read_entry(e)
        if data is None:
            continue
        with open(out_path, "wb") as o:
            o.write(data)
        manifest[name] = dict(size=len(data), comp=e["comp"], usize=e["usize"])
        count += 1
    except Exception as ex:
        manifest[name] = dict(error=str(ex))
print(f"extracted {count}/{len(entries)}")
with open(os.path.join(OUT, "manifest.json"), "w") as m:
    json.dump(manifest, m, indent=1)
