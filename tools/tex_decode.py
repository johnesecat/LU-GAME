#!/usr/bin/env python3
"""Decode UE5 .ubulk textures (BC1/DXT1, BC3/DXT5, BC5, plus raw RGBA/BGRA/G8) to PNG.

Reads texture dimensions + pixel format from the .uexp, then decodes the .ubulk.
Outputs PNGs into web/assets/textures/ preserving the game's logical paths.
"""
import os, re, struct, sys, zlib
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

# ---- BC decoders (operate on 4x4 blocks) ----
def decode_bc1(data, w, h):
    out = bytearray(w*h*4)
    bx, by = (w+3)//4, (h+3)//4
    pos = 0
    for j in range(by):
        for i in range(bx):
            if pos+8 > len(data): return bytes(out)
            c0, c1, bits = struct.unpack_from("<HHI", data, pos); pos += 8
            def rgb565(c):
                r = ((c >> 11) & 0x1F) << 3; g = ((c >> 5) & 0x3F) << 2; b = (c & 0x1F) << 3
                return r, g, b
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
                        r,g,b,a = pal[idx]
                        o = (y*w+x)*4
                        out[o:o+4] = bytes((r,g,b,a))
    return bytes(out)

def decode_bc3(data, w, h):
    out = bytearray(w*h*4)
    bx, by = (w+3)//4, (h+3)//4
    pos = 0
    for j in range(by):
        for i in range(bx):
            if pos+16 > len(data): return bytes(out)
            a0, a1, abits = struct.unpack_from("<BBH", data, pos)
            c0, c1, cbits = struct.unpack_from("<HHI", data, pos+4); pos += 16
            # alpha palette
            apal = [a0, a1]
            if a0 > a1:
                for k in range(6):
                    apal.append((6-k)*a0 + (k+1)*a1)  # placeholder, fixed below
                apal = [a0, a1] + [((6-k)*a0 + (k+1)*a1)//7 for k in range(6)]
            else:
                apal = [a0, a1] + [((4-k)*a0 + k*a1)//5 for k in range(1,5)] + [0, 255]
            def rgb565(c):
                r = ((c >> 11) & 0x1F) << 3; g = ((c >> 5) & 0x3F) << 2; b = (c & 0x1F) << 3
                return r, g, b
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
    out = bytearray(w*h*4)
    bx, by = (w+3)//4, (h+3)//4
    pos = 0
    for j in range(by):
        for i in range(bx):
            if pos+16 > len(data): return bytes(out)
            r0, r1, rbits = struct.unpack_from("<BBH", data, pos)
            g0, g1, gbits = struct.unpack_from("<BBH", data, pos+8); pos += 16
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

# ---- find texture dims from uexp ----
def tex_info(uexp_path):
    d = open(uexp_path, "rb").read()
    m = re.search(rb"PF_[A-Z0-9]+", d)
    if not m: return None
    fmt = m.group().decode()
    # dimensions: look for the "SizeX"/"SizeY" pattern in the serialized data.
    # UE5 serializes Texture2D with two int32 dims right before the pixel format name
    # in the cooked export. Search for plausible (w,h) pairs near the PF_ string.
    pf_at = m.start()
    # The dims are typically 8 bytes before the PF_ string (SizeX, SizeY as i32)
    for back in range(8, 64, 4):
        if pf_at - back >= 8:
            w, h = struct.unpack_from("<ii", d, pf_at - back)
            if 0 < w <= 16384 and 0 < h <= 16384 and w % 4 == 0 and h % 4 == 0:
                return fmt, w, h
    return fmt, None, None

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
    fmt, w, h = info
    data = open(ubulk, "rb").read()
    rel = n[len("HDT/Content/"):].replace("//", "/")
    out_path = os.path.join(DST, rel[:-6] + ".png").replace("/", os.sep)
    try:
        if w is None:
            stats[f"{fmt}:no-dims"] += 1
            continue
        if fmt == "PF_DXT1":
            need = ((w+3)//4)*((h+3)//4)*8
            if len(data) < need: stats[f"{fmt}:short"] += 1; continue
            rgba = decode_bc1(data, w, h)
        elif fmt == "PF_DXT5":
            need = ((w+3)//4)*((h+3)//4)*16
            if len(data) < need: stats[f"{fmt}:short"] += 1; continue
            rgba = decode_bc3(data, w, h)
        elif fmt == "PF_BC5":
            need = ((w+3)//4)*((h+3)//4)*16
            if len(data) < need: stats[f"{fmt}:short"] += 1; continue
            rgba = decode_bc5(data, w, h)
        elif fmt in ("PF_B8G8R8A8", "PF_R8G8B8A8", "PF_G8"):
            rgba = decode_raw(data, w, h, fmt)
            if rgba is None: stats[f"{fmt}:raw"] += 1; continue
        else:
            stats[f"{fmt}:skip"] += 1
            continue
        png_write(out_path, w, h, rgba)
        converted += 1
        stats[fmt] += 1
    except Exception as ex:
        stats[f"err:{str(ex)[:40]}"] += 1
print(f"converted {converted} textures")
for k, v in stats.most_common(20):
    print(f"  {v:5d}  {k}")
