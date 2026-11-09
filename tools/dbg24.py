import struct
data = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb").read()
# The file at offset 156436480 starts with "00 00 00 00 00 00 00 00 98 23 2F 00 00 00 00 00 F6 69 61 00..."
# That's an inline FPakEntry header! offset=0, size=0x2F2398=3088280, usize=0x61F6F6?? wait:
# bytes: [0-7]=00 (offset), [8-15]="98 23 2F 00 00 00 00 00"=0x2F2398=3088280 (size), 
# [16-23]="F6 69 61 00 00 00 00 00"=0x6169F6=6384118 (usize) ✓ matches!
# [24-27]="01 00 00 00"=1 (comp=Zlib), [28-47]=hash, [48-51]=blocks, [52]=enc, [53+]=cbs+block table
# So for compressed files, the inline header is followed by block info!
# Header layout: offset(8) size(8) usize(8) comp(4) hash(20) blocks(4) enc(1) cbs(4) then block table
# Let me parse: blocks at 48-51, enc at 52, cbs at 53-56, then blocks*16 bytes of (start,end) pairs
f = data
off = 156436480
h = f[off:off+57]
o, s, u = struct.unpack_from("<qqq", h, 0)
comp, = struct.unpack_from("<i", h, 24)
blocks, = struct.unpack_from("<I", h, 48)
enc = h[52]
cbs, = struct.unpack_from("<I", h, 53)
print(f"inline hdr: off={o} size={s} usize={u} comp={comp} blocks={blocks} enc={enc} cbs={cbs}")
# block table
bt = off + 57
for i in range(min(blocks, 3)):
    s0, e0 = struct.unpack_from("<qq", f, bt + i*16)
    print(f"block[{i}]: start={s0} end={e0} len={e0-s0}")
# The block starts are RELATIVE to the entry offset. Data begins after the header+block table.
data_start = bt + blocks*16
print("data starts at", data_start, "(entry offset +", data_start - off, ")")
print("first data bytes:", " ".join(f"{b:02X}" for b in f[data_start:data_start+16]))
import zlib
# try raw deflate on first block
s0, e0 = struct.unpack_from("<qq", f, bt)
raw = f[off+s0:off+e0] if s0 > 0 else f[data_start:data_start+ (e0-s0)]
print("block0 raw len:", len(raw))
try:
    d = zlib.decompressobj(-15)
    out = d.decompress(raw)
    print("raw deflate OK:", len(out))
except Exception as e:
    print("raw deflate fail:", e)
try:
    out = zlib.decompress(raw)
    print("zlib OK:", len(out))
except Exception as e:
    print("zlib fail:", e)
