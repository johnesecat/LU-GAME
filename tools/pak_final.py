#!/usr/bin/env python3
"""Final UE5 pak v11 extractor for HDT-WindowsNoEditor.pak.

Key fixes vs earlier attempts:
- Compressed entries: data starts at entry_offset + 57 + 16*NumBlocks
  (inline FPakEntry header = 48 bytes fixed + NumBlocks(4) + flags(1) + cbs(4),
  then a 16-byte (u64,u64) block table), NOT at the entry offset itself.
- Uncompressed entries: data starts at entry_offset + 53.
- Multi-block zlib: blocks are back-to-back standard zlib streams; chain them.
"""
import struct, os, zlib, json, sys
from collections import Counter

PAK = r"HDT\Content\Paks\HDT-WindowsNoEditor.pak"
OUT = "extracted"

data = open(PAK, "rb").read()
fsize = len(data)

magic_at = data.rfind(b"\xE1\x12\x6F\x5A", fsize - 4096)
assert magic_at > 0, "pak footer magic not found"
index_offset, index_size = struct.unpack_from("<qq", data, magic_at + 8)
idx = data[index_offset:index_offset+index_size]

def rd_i32(b, p): return struct.unpack_from("<i", b, p)[0], p+4
def rd_i64(b, p): return struct.unpack_from("<q", b, p)[0], p+8
def rd_fstr(b, p):
    n, p = rd_i32(b, p)
    s = b[p:p+n-1].decode("utf-8", "replace") if n > 0 else ""
    return s, p+n

p = 0
mount, p = rd_fstr(idx, p)
num_entries, p = rd_i32(idx, p)
seed, p = rd_i64(idx, p)
has_phi, p = rd_i32(idx, p)
if has_phi: p += 16 + 20
has_fdi, p = rd_i32(idx, p)
fdi_off, p = rd_i64(idx, p)
fdi_size, p = rd_i64(idx, p)
p += 20
enc_count, p = rd_i32(idx, p)
ENC_BASE = p

fdi = data[fdi_off:fdi_off+fdi_size]
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

def decode_entry(buf, pos):
    flags, = struct.unpack_from("<I", buf, pos); pos += 4
    cbs = (flags & 0x3F) << 11
    if (flags & 0x3F) == 0x3F:
        cbs, = struct.unpack_from("<I", buf, pos); pos += 4
    blocks = (flags >> 6) & 0xFFFF
    encrypted = (flags >> 22) & 1
    comp = (flags >> 23) & 0x3F
    size32 = (flags >> 29) & 1
    usize32 = (flags >> 30) & 1
    off32 = (flags >> 31) & 1
    if off32:
        offset, = struct.unpack_from("<I", buf, pos); pos += 4
    else:
        offset, = struct.unpack_from("<Q", buf, pos); pos += 8
    if usize32:
        usize, = struct.unpack_from("<I", buf, pos); pos += 4
    else:
        usize, = struct.unpack_from("<Q", buf, pos); pos += 8
    csize = usize
    if comp != 0:
        if size32:
            csize, = struct.unpack_from("<I", buf, pos); pos += 4
        else:
            csize, = struct.unpack_from("<Q", buf, pos); pos += 8
    return dict(offset=offset, usize=usize, csize=csize, comp=comp,
                blocks=blocks, encrypted=encrypted)

entries = {}
for name, enc in files:
    entries[name] = decode_entry(idx, ENC_BASE + enc)
print(f"index: {len(entries)} entries", flush=True)

def extract_entry(e):
    off = e["offset"]
    if e["comp"] == 0:
        blob = data[off+53 : off+53+e["usize"]]
        if len(blob) != e["usize"]:
            raise RuntimeError(f"short read {len(blob)}/{e['usize']}")
        return blob
    # compressed (zlib): inline header + block table precede the data
    num_blocks, = struct.unpack_from("<I", data, off+48)
    data_start = off + 57 + 16*num_blocks
    region = data[data_start : data_start + e["csize"]]
    out = b""
    pos = 0
    while len(out) < e["usize"] and pos < len(region):
        d = zlib.decompressobj()
        chunk = d.decompress(region[pos:])
        out += chunk
        if d.eof:
            rest = d.unused_data
            consumed = len(region) - pos - len(rest)
            if consumed == 0:
                raise RuntimeError("zero-consumption zlib stream")
            pos += consumed
        else:
            break
    if len(out) < e["usize"]:
        raise RuntimeError(f"short decompress {len(out)}/{e['usize']}")
    return out[:e["usize"]]

# ---- self-test on the known compressed entry ----
test_name = "Engine//GlobalShaderCache-PCD3D_SM5.bin"
te = entries.get(test_name)
if te:
    try:
        blob = extract_entry(te)
        print(f"SELF-TEST {test_name}: {len(blob)} bytes (expect {te['usize']})", flush=True)
        assert len(blob) == te["usize"], "length mismatch"
    except Exception as ex:
        print(f"SELF-TEST FAILED: {ex}", flush=True)
        sys.exit(1)

# ---- full extraction ----
ok = 0
errors = Counter()
manifest = {}
for name, e in entries.items():
    out_path = os.path.join(OUT, name.replace("/", os.sep))
    d = os.path.dirname(out_path)
    if d:
        os.makedirs(d, exist_ok=True)
    try:
        blob = extract_entry(e)
        with open(out_path, "wb") as o:
            o.write(blob)
        manifest[name] = len(blob)
        ok += 1
    except Exception as ex:
        errors[str(ex)[:120]] += 1
        manifest[name] = -1
print(f"extracted {ok}/{len(entries)}", flush=True)
for e_, n in errors.most_common(10):
    print(f"  {n}x {e_}", flush=True)
json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)

# ---- inventory ----
prefixes = Counter()
exts = Counter()
game_files = []
for name in entries:
    top = name.split("/")[0] if "/" in name else "(root)"
    prefixes[top] += 1
    ext = os.path.splitext(name)[1].lower()
    exts[ext] += 1
    if not name.startswith("Engine/"):
        game_files.append(name)
print("\ntop-level prefixes:", dict(prefixes.most_common(10)))
print("extensions:", dict(exts.most_common(15)))
print(f"\ngame (non-Engine) files: {len(game_files)}")
for n in sorted(game_files)[:80]:
    print("  ", n)
with open(os.path.join(OUT, "_filelist.txt"), "w") as fl:
    for n in sorted(entries):
        fl.write(n + "\n")

# ---- PNG dims of presets ----
def png_dims(path):
    with open(path, "rb") as fh:
        head = fh.read(33)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", head[16:24])
        return w, h
    return None

import glob
for pat in [r"HDT\Content\Presets\Outfits\Default\*.png", r"HDT\Content\Presets\Characters\*"]:
    for f in glob.glob(pat):
        print("PNG:", os.path.basename(f), png_dims(f))
