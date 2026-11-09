import struct
data = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb").read()
idx = data[339628863:339628863+165602]
# The manifest only recorded comp for OK files. Let me re-decode and count comp slots for all.
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
if has_phi:
    p += 16 + 20
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

from collections import Counter
comps = Counter()
blocks_dist = Counter()
for name, enc in files:
    pos = ENC_BASE + enc
    flags, = struct.unpack_from("<I", idx, pos)
    comp = (flags >> 23) & 0x3F
    blocks = (flags >> 6) & 0xFFFF
    comps[comp] += 1
    blocks_dist[blocks] += 1
print("comp slots:", comps)
print("blocks dist (top):", blocks_dist.most_common(10))
