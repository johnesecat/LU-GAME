#!/usr/bin/env python3
"""UE5 pak v11 extractor — FDI enc values are relative to encoded-region start (index+110)."""
import struct, sys, os, zlib, json

PAK = r"HDT\Content\Paks\HDT-WindowsNoEditor.pak"
OUT = "extracted"

data = open(PAK, "rb").read()
fsize = len(data)

magic_at = data.rfind(b"\xE1\x12\x6F\x5A", fsize - 4096)
magic, version = struct.unpack_from("<II", data, magic_at)
index_offset, index_size = struct.unpack_from("<qq", data, magic_at + 8)
print(f"pak v{version}, index at {index_offset} size {index_size}", flush=True)

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
ENC_BASE = p  # encoded entries start here
print(f"mount={mount} entries={num_entries} encBase={ENC_BASE} encCount={enc_count}", flush=True)

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
print(f"FDI files: {len(files)}", flush=True)

def decode_entry(buf, pos):
    flags, = struct.unpack_from("<I", buf, pos)
    pos += 4
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
    block_sizes = []
    if blocks > 1 or (blocks == 1 and encrypted):
        for i in range(blocks):
            bs, = struct.unpack_from("<I", buf, pos); pos += 4
            block_sizes.append(bs)
    return dict(offset=offset, usize=usize, csize=csize, comp=comp, blocks=blocks,
                encrypted=encrypted, cbs=cbs, block_sizes=block_sizes)

entries = {}
bad = 0
for name, enc in files:
    try:
        entries[name] = decode_entry(idx, ENC_BASE + enc)
    except Exception:
        bad += 1
print(f"decoded {len(entries)-bad}, bad {bad}", flush=True)
for name, e in list(entries.items())[:3]:
    print(name, e["offset"], e["usize"], e["csize"], e["comp"], e["blocks"], flush=True)

# validate: all offsets within pak, sizes sane
ok = 0
for name, e in entries.items():
    if e["offset"] + e["csize"] <= fsize and e["usize"] < 500000000:
        ok += 1
print(f"sane entries: {ok}/{len(entries)}", flush=True)

count = 0
manifest = {}
for name, e in entries.items():
    out_path = os.path.join(OUT, name.replace("/", os.sep))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    try:
        if e["comp"] == 0:
            blob = data[e["offset"]:e["offset"]+e["usize"]]
        elif e["blocks"] <= 1:
            raw = data[e["offset"]:e["offset"]+e["csize"]]
            blob = zlib.decompress(raw) if e["comp"] == 1 else raw
        else:
            blob = b""
            pos = e["offset"]
            for bs in e["block_sizes"]:
                raw = data[pos:pos+bs]
                blob += zlib.decompress(raw) if e["comp"] == 1 else raw
                pos += bs
        with open(out_path, "wb") as o:
            o.write(blob)
        manifest[name] = dict(size=len(blob), comp=e["comp"], usize=e["usize"])
        count += 1
    except Exception as ex:
        manifest[name] = dict(error=str(ex))
print(f"extracted {count}/{len(entries)}", flush=True)
with open(os.path.join(OUT, "manifest.json"), "w") as m:
    json.dump(manifest, m, indent=1)
