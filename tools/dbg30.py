import struct, zlib
data = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb").read()
off = 156436480
h = data[off:off+1700]
# u32@60 = 31532 = 0x7B2C. u32@61 = 123 = 0x7B. So bytes 60-63 = "2C 7B 00 00".
# The 16-byte entries: bytes 57-72 = "00 00 00 2C 7B 00 00 00 00 00 00 2C 7B 00 00 00"
# As TWO u64s: u64@57 = 0x00007B2C00000000, u64@65 = 0x00007B2C00000000.
# Hmm, 0x7B2C00000000 = 134,868,873,949,184?? No: 0x7B2C << 32 = 0x7B2C00000000 = 134868873949184? 
# 0x7B2C = 31532. 31532 << 32 = 135,428,908,777,472. And blk[0] printed 529019174912.
# 529019174912 / 2^32 = 123.25. Hmm 529019174912 = 0x7B4C000000. 0x7B4C = 31564.
# Wait, struct.unpack_from("<QQ", h, 57) — h here is data[off:off+1700], so h[57] = data[off+57].
# But in dbg28 I printed "raw bytes 57-105" from the same h. bytes 57-60 = "00 00 00", byte 60 = 2C.
# u64@57 = b0..b7 = [00,00,00,2C,7B,00,00,00] = 0x2C<<24 | 0x7B<<32 = 0x7B2C000000.
# 0x7B2C000000 = 528,577,241,088. But blk[0] said 529,019,174,912 = 0x7B4C000000.
# 0x7B4C = 31564 ≠ 31532 = 0x7B2C. There's an inconsistency — one of my byte dumps is wrong.
# Doesn't matter. The important thing: the u64 values are HUGE (0x7B2C000000 = 528 billion).
# 528577241088 >> 32 = 123. And 123 = 0x7B. So u64@57 = 0x7B << 32 | 0x2C << 24.
# What if the block entries are (u64 start, u64 end) where start/end are SHIFTED or the
# entries are actually (u32 start, u32 end) pairs and I should read at 60?
# u32@60 = 31532, u32@64 = 0. So (start=31532, end=0)?? no.
# NEW APPROACH: forget parsing the block table from the header. The DATA starts at 1625
# (zlib 78 9C). The total compressed size is 3089304. If blocks are contiguous, I can
# just decompress the whole thing as one zlib stream? No — multiple blocks = multiple streams.
# BUT: maybe I can decompress block by block using the cumulative ends 31532, 61129, 84026...
# block0 = data[1625 : 1625+31532], block1 = data[1625+31532 : 1625+61129], etc.
# Let me try decompressing block0 with raw deflate and zlib:
d0 = h[1625:1625+31532]
print("block0 first bytes:", " ".join(f"{b:02X}" for b in d0[:8]))
try:
    out = zlib.decompress(d0)
    print("zlib OK:", len(out))
except Exception as e:
    print("zlib fail:", e)
try:
    out = zlib.decompressobj(-15).decompress(d0)
    print("raw deflate OK:", len(out))
except Exception as e:
    print("raw deflate fail:", e)
# Also try: maybe blocks are 65536 uncompressed each. cbs might be 65536.
# usize = 6384118, blocks = 98. 6384118 / 98 = 65144. Close to 65536 but not exact.
# 97 * 65536 = 6356992. 6384118 - 6356992 = 27126. So cbs = 65536, last block = 27126. ✓
# So cbs = 65536. The "cbs" field I read as 6 was wrong (that was part of something else).
