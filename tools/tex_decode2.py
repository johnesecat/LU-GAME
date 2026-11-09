#!/usr/bin/env python3
"""Decode UE5 .ubulk textures to PNG — FIXED.

Fixes vs previous version:
1. BC3/DXT5 alpha + BC5 red/green: the 48-bit index fields were read as u16 (<BBH),
   garbling every 4x4 block ("tiny boxes with red/blue tint"). Now read as 48-bit LE.
2. Dimensions now parsed from the real mip table in the .uexp instead of a heuristic:
   after "PF_XXX\\0": +0 i32, +4 i32 (NumMips), +8 i32, then 36-byte mip entries:
     flags u32 @+0, ElementCount u32 @+4, SizeOnDisk u32 @+8, OffsetInFile i64 @+12,
     SizeX i32 @+20, SizeY i32 @+24, SizeZ i32 @+28, ? i32 @+32
   mip0's SizeX/SizeY are the full texture dims; ElementCount is mip0's byte size.
3. Data read from ubulk[OffsetInFile : OffsetInFile+ElementCount].
"""
import os, re, struct, zlib
from collections import Counter

SRC = "extracted"
DST = "web/assets/textures"

def png_write(path, w, h, rgba):
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + rgba[y*w*4:(y+1)*w*4] for y in range(h))
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 6))
           + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)

def decode_bc1(data, w, h):
    """DXT1/BC1: 8-byte blocks. c0,c1 u16 RGB565 + 32 bits of 2-bit indices."""
    out = bytearray(w*h*4)
    bx, by = (w+3)//4, (h+3)//4
    pos = 0
    for j in range(by):
        for i in range(bx):
            if pos+8 > len(data): return bytes(out)
            c0, c1, bits = struct.unpack_from("<HHI", data, pos); pos += 8
            def rgb565(c):
                return (((c >> 11) & 0x1F) * 255) // 31, (((c >> 5) & 0x3F) * 255) // 63, ((c & 0x1F) * 255) // 31
            r0,g0,b0 = rgb565(c0); r1,g1,b1 = rgb565(c1)
            if c0 > c1:
                pal = [(r0,g0,b0,255),(r1,g1,b1,255),
                       ((2*r0+r1)//3,(2*g0+g1)//3,(2*b0+b1)//3,255),
                       ((r0+2*r1)//3,(g0+2*g1)//3,(b0+2*b1)//3,255)]
            else:
                pal = [(r0,g0,b0,255),(r1,g1,b1,255),
                       ((r0+r1)//2,(g0+g1)//2,(b0+b1)//2,255),(0,0,0,0)]
            for py in range(4):
                for px in range(4):
                    x, y = i*4+px, j*4+py
                    if x < w and y < h:
                        idx = (bits >> (2*(py*4+px))) & 3
                        o = (y*w+x)*4
                        out[o:o+4] = bytes(pal[idx])
    return bytes(out)

def decode_bc3(data, w, h):
    """DXT5/BC3: 16-byte blocks. 8-byte alpha (2 endpoints + 48-bit indices) + 8-byte color."""
    out = bytearray(w*h*4)
    bx, by = (w+3)//4, (h+3)//4
    pos = 0
    for j in range(by):
        for i in range(bx):
            if pos+16 > len(data): return bytes(out)
            # alpha: a0, a1 bytes, then 48-bit LE index field (6 bytes)
            a0 = data[pos]; a1 = data[pos+1]
            abits = int.from_bytes(data[pos+2:pos+8], "little")
            c0, c1, cbits = struct.unpack_from("<HHI", data, pos+8)
            pos += 16
            if a0 > a1:
                apal = [a0, a1] + [((6-k)*a0 + (k+1)*a1)//7 for k in range(6)]
            else:
                apal = [a0, a1] + [((4-k)*a0 + k*a1)//5 for k in range(1,5)] + [0, 255]
            def rgb565(c):
                return (((c >> 11) & 0x1F) * 255) // 31, (((c >> 5) & 0x3F) * 255) // 63, ((c & 0x1F) * 255) // 31
            r0,g0,b0 = rgb565(c0); r1,g1,b1 = rgb565(c1)
            pal = [(r0,g0,b0),(r1,g1,b1),
                   ((2*r0+r1)//3,(2*g0+g1)//3,(2*b0+b1)//3),
                   ((r0+2*r1)//3,(g0+2*g1)//3,(b0+2*b1)//3)]
            for py in range(4):
                for px in range(4):
                    x, y = i*4+px, j*4+py
                    if x < w and y < h:
                        k = py*4+px
                        ai = (abits >> (3*k)) & 7
                        ci = (cbits >> (2*k)) & 3
                        r,g,b = pal[ci]
                        o = (y*w+x)*4
                        out[o:o+4] = bytes((r,g,b,apal[ai]))
    return bytes(out)

def decode_bc5(data, w, h):
    """BC5: 16-byte blocks. Two 8-byte channels (red, green), each 2 endpoints + 48-bit indices."""
    out = bytearray(w*h*4)
    bx, by = (w+3)//4, (h+3)//4
    pos = 0
    for j in range(by):
        for i in range(bx):
            if pos+16 > len(data): return bytes(out)
            r0 = data[pos]; r1 = data[pos+1]
            rbits = int.from_bytes(data[pos+2:pos+8], "little")
            g0 = data[pos+8]; g1 = data[pos+9]
            gbits = int.from_bytes(data[pos+10:pos+16], "little")
            pos += 16
            def pal8(a, b):
                if a > b:
                    return [a, b] + [((6-k)*a + (k+1)*b)//7 for k in range(6)]
                return [a, b] + [((4-k)*a + k*b)//5 for k in range(1,5)] + [0, 255]
            rp = pal8(r0, r1); gp = pal8(g0, g1)
            for py in range(4):
                for px in range(4):
                    x, y = i*4+px, j*4+py
                    if x < w and y < h:
                        k = py*4+px
                        r = rp[(rbits >> (3*k)) & 7]; g = gp[(gbits >> (3*k)) & 7]
                        o = (y*w+x)*4
                        out[o:o+4] = bytes((r, g, 255, 255))
    return bytes(out)

def decode_raw(data, w, h, fmt):
    n = w*h*4
    if fmt == "PF_B8G8R8A8":
        out = bytearray(n)
        for i in range(0, min(n, len(data)), 4):
            out[i] = data[i+2]; out[i+1] = data[i+1]; out[i+2] = data[i]; out[i+3] = data[i+3]
        return bytes(out)
    if fmt == "PF_R8G8B8A8":
        return bytes(data[:n])
    if fmt == "PF_G8":
        out = bytearray(n)
        for i in range(min(w*h, len(data))):
            v = data[i]; out[i*4:i*4+4] = bytes((v,v,v,255))
        return bytes(out)
    return None

BLOCK = {"PF_DXT1": 8, "PF_DXT5": 16, "PF_BC5": 16, "PF_BC6H": 16, "PF_BC7": 16}

def tex_info(uexp_path):
    """Parse the mip table after the PF_ string. Returns (fmt, w, h, count, offset)."""
    d = open(uexp_path, "rb").read()
    m = re.search(rb"PF_[A-Z0-9]+\x00", d)
    if not m: return None
    fmt = m.group()[:-1].decode()
    at = m.end()
    if at + 40 > len(d): return (fmt, None, None, None, None)
    # mip0 entry starts at +12; ElementCount @+16, OffsetInFile(i64) @+24, SizeX @+32, SizeY @+36
    try:
        element_count, = struct.unpack_from("<I", d, at+16)
        offset, = struct.unpack_from("<q", d, at+24)
        size_x, = struct.unpack_from("<i", d, at+32)
        size_y, = struct.unpack_from("<i", d, at+36)
    except struct.error:
        return (fmt, None, None, None, None)
    return (fmt, size_x, size_y, element_count, offset)

fl = open(os.path.join(SRC, "_filelist.txt")).read().splitlines()
stats = Counter()
converted = 0
for n in fl:
    if not n.endswith(".ubulk"): continue
    uexp = os.path.join(SRC, n[:-6] + ".uexp").replace("/", os.sep)
    ubulk = os.path.join(SRC, n).replace("/", os.sep)
    if not os.path.exists(uexp): continue
    info = tex_info(uexp)
    if not info: continue
    fmt, w, h, count, offset = info
    if w is None or w <= 0 or h <= 0 or w > 16384 or h > 16384:
        stats[f"{fmt}:bad-dims"] += 1
        continue
    data = open(ubulk, "rb").read()
    rel = n[len("HDT/Content/"):].replace("//", "/")
    out_path = os.path.join(DST, rel[:-6] + ".png").replace("/", os.sep)
    try:
        if fmt in BLOCK:
            need = ((w+3)//4)*((h+3)//4)*BLOCK[fmt]
            if count and count != need:
                stats[f"{fmt}:count-mismatch({count}!={need})"] += 1
                # trust the mip table's ElementCount when it disagrees: recompute dims from it
                continue
            if offset + need > len(data):
                stats[f"{fmt}:short-ubulk"] += 1
                continue
            blob = data[offset:offset+need]
            if fmt == "PF_DXT1":
                rgba = decode_bc1(blob, w, h)
            elif fmt == "PF_DXT5":
                rgba = decode_bc3(blob, w, h)
            elif fmt == "PF_BC5":
                rgba = decode_bc5(blob, w, h)
            else:
                stats[f"{fmt}:unsupported"] += 1
                continue
        elif fmt in ("PF_B8G8R8A8", "PF_R8G8B8A8", "PF_G8"):
            need = w*h*(4 if "A8" in fmt else 1)
            if offset + need > len(data):
                stats[f"{fmt}:short-ubulk"] += 1
                continue
            blob = data[offset:offset+need]
            rgba = decode_raw(blob, w, h, fmt)
            if rgba is None:
                stats[f"{fmt}:raw"] += 1
                continue
        else:
            stats[f"{fmt}:skip"] += 1
            continue
        png_write(out_path, w, h, rgba)
        converted += 1
        stats[fmt] += 1
    except Exception as ex:
        stats[f"err:{str(ex)[:60]}"] += 1
print(f"converted {converted} textures")
for k, v in stats.most_common(25):
    print(f"  {v:5d}  {k}")
