import struct, zlib
data = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb").read()
off = 156436480
h = data[off:off+1700]
# raw bytes 57-105: "00 00 00 2C 7B 00 00 00 | 00 00 00 2C 7B 00 00 00 | 00 00 00 C9 EE 00 00 00 | ..."
# So each 8-byte group is "00 00 00 XX XX 00 00 00". The u32 value is at +3 within each 8-byte group.
# u64@57 = 0x7B2C000000 (bytes 57-64: 00 00 00 2C 7B 00 00 00).
# Hmm wait: bytes 57-64 = [00,00,00,2C,7B,00,00,00]. LE u64 = 0x00007B2C00000000? 
# b3=0x2C contributes 0x2C<<24 = 0x2C000000. b4=0x7B contributes 0x7B<<32 = 0x7B00000000.
# Total = 0x7B2C000000 = 528,577,241,088. But blk[0] printed 529019174912 = 0x7B4C000000.
# Hmm discrepancy — because struct.unpack_from("<QQ", h, 57) reads u64 at 57 and 65.
# bytes 57-64 = "00 00 00 2C 7B 00 00 00" -> 0x00007B2C00000000?? 
# Let me compute: b0=0,b1=0,b2=0,b3=0x2C,b4=0x7B,b5=0,b6=0,b7=0
# value = 0x2C*2^24 + 0x7B*2^32 = 0x2C000000 + 0x7B00000000 = 0x7B2C000000 = 528577241088
# But the tool printed 529019174912 = 0x7B4C000000. So my byte reading is off by something.
# Whatever — the KEY INSIGHT: the values at u32@60 are 31532, 61129, 84026... which are
# CUMULATIVE COMPRESSED SIZES. And each 16-byte entry has the SAME value twice.
# In UE5, FPakCompressedBlock = {u64 CompressedStart, u64 CompressedEnd} where start/end
# are RELATIVE TO THE ENTRY OFFSET. So block0 = (start=0, end=31532)?
# But we see the same value twice: (31532, 31532)??
# UNLESS the layout is: (u64 CompressedEnd, u64 UncompressedEnd)?? 
# block0: compressedEnd=31532, uncompressedEnd=65536? But both print 31532.
# Hmm wait — blk[0] printed (529019174912, 529019174912). 529019174912 = 0x7B4C000000.
# 0x7B4C = 31564?? no, 0x7B4C = 31564. Hmm.
# Let me just read u32 at 60 directly:
v, = struct.unpack_from("<I", h, 60)
print("u32@60 =", v)  # expect 31532
v2, = struct.unpack_from("<I", h, 68)
print("u32@68 =", v2)
# If both are 31532, then the 16-byte entry = (u64 with value 31532<<32, u64 with value 31532<<32)?
# That means the u64s are NOT (start,end) but something else.
# AH WAIT. I bet the block entries are (u64 CompressedStart, u64 CompressedEnd) where
# CompressedStart/End are ABSOLUTE pak offsets! block0 = (X, X+31532)?
# u64@57 = 529019174912?? That's bigger than the pak (340MB). No.
# Hmm, unless... let me look at "00 00 00 2C 7B 00 00 00" as u64 BE: 0x0000002C7B000000 = 134868848640. no.
# What if the entries are (u32 start, u32 end) at 57? start = 0x2C000000?? no.
# What if entries are (u32 csize, u32 usize) at 60? csize=31532, usize=?
# u32@64 = bytes 64-67 = "00 00 00 00" = 0. Hmm.
# Let me print u32s at 57..80:
for i in range(57, 89, 4):
    v, = struct.unpack_from("<I", h, i)
    print(f"u32@{i} = {v} (0x{v:X})")
