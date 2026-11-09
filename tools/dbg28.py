import struct, zlib
data = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb").read()
off = 156436480
h = data[off:off+1700]
# u32 values at 60, 76, 92, ... (16-byte spacing): 31532, 61129, 84026, 109127, 139091, 168066
# Differences: 61129-31532=29597, 84026-61129=22897, 109127-84026=25101, 139091-109127=29964, 168066-139091=28975
# These are ~25-30KB — compressed block sizes! And the u32 at 60 = 31532... 
# Wait, earlier I computed u32@60 = 11371 but now it says 31532?! Let me recheck.
# bytes 56-63: "00 00 00 00 2C 7B 00 00" -> [56]=00 [57]=00 [58]=00 [59]=00 [60]=2C [61]=7B [62]=00 [63]=00
# u32@60 = LE of [2C,7B,00,00] = 0x00007B2C = 31532! (I said 11371 before — 0x7B2C = 31532, not 11371. 11371 = 0x2C7B.)
# OK so u32@60 = 31532. And the sequence 31532, 61129, 84026... are CUMULATIVE block ends!
# block0: 0..31532 (csize 31532), block1: 31532..61129 (csize 29597), etc.
# And each 16-byte entry = (u64 pad, u32 end, u32 pad)? bytes 56-71: "00 00 00 00 2C 7B 00 00 | 00 00 00 00 2C 7B 00 00"
# Hmm both halves identical! u32@60 = 31532 AND u32@68 = 31532.
# So entry = (u64, u64) where both u64s equal 0x7B2C00000000?? no...
# bytes 56-71: [56..63]="00 00 00 00 2C 7B 00 00" [64..71]="00 00 00 00 2C 7B 00 00"
# u64@56 = 0x00007B2C00000000, u64@64 = 0x00007B2C00000000. Both equal!
# In UE5, FPakCompressedBlock = (u64 CompressedStart, u64 CompressedEnd). If both are equal,
# the block has length 0. That can't be right.
# BUT WAIT: what if these are (CompressedEnd, UncompressedEnd)?? 
# u64@56 = 0x7B2C00000000... no.
# What if the u64s are actually (start<<32 | end)?? 0x00007B2C00000000 = start=0x7B2C, end=0? no.
# Hmm, what if I have the wrong header size and the table actually starts elsewhere?
# Data starts at 1625 (zlib magic 78 9C found there). Table region = 57..1625 = 1568 bytes = 98*16.
# So the table IS 98 entries of 16 bytes starting at 57.
# entry_i = bytes 57+16i .. 57+16i+16. entry0 = bytes 57-72.
# bytes 57-72: [57]=00 [58]=00 [59]=00 [60]=2C [61]=7B [62]=00 [63]=00 [64]=00 [65]=00 [66]=00 [67]=00 [68]=2C [69]=7B [70]=00 [71]=00
# Hmm wait, that gives u64@57 = bytes 57-64 = "00 00 00 2C 7B 00 00 00" = 0x00007B2C000000?? 
# LE u64 of [00,00,00,2C,7B,00,00,00] = 0x00007B2C00000000. Hmm.
# Let me just print raw bytes 57-105 to be 100% sure.
print("raw bytes 57-105:")
print(" ".join(f"{b:02X}" for b in h[57:105]))
# And check: maybe the header is 53 bytes (not 57) and the table starts at 53?
# Standard UE5 FPakEntry serialized size for compressed files:
#   Offset(8) + Size(8) + UncompressedSize(8) + CompressionMethod(4) + Hash(20) + 
#   NumBlocks(4) + Flags(1) + CompressionBlockSize(4) + Blocks(16*N)
# = 8+8+8+4+20+4+1+4 = 57. ✓ table at 57.
# So entry0 = (u64@57, u64@65): u64@57 = bytes 57-64, u64@65 = bytes 65-72.
# bytes 57-64 = "00 00 00 2C 7B 00 00 00" -> LE = 0x0000007B2C000000?? 
# Ugh, let me be very careful: LE u64 from bytes b0..b7 = b0 + b1<<8 + ... + b7<<56.
# b0=00 b1=00 b2=00 b3=2C b4=7B b5=00 b6=00 b7=00
# = 0x2C<<24 + 0x7B<<32 = 0x7B2C000000 = 528,577,241,088?? 
# Hmm: 0x2C << 24 = 0x2C000000, 0x7B << 32 = 0x7B00000000. Sum = 0x7B2C000000 = 528577241088.
# That's not 31532.
# BUT if the u64 were at 60: b0=2C b1=7B b2..b7=00 -> 0x7B2C = 31532 ✓
# So the values ARE at 60, 68, 76... but the table starts at 57?? That means each entry is
# (3 bytes pad, u64 value, 5 bytes pad)?? Nonsense.
# UNLESS the table starts at 60! Then 60 + 98*16 = 60+1568 = 1628 ≠ 1625.
# OR the table starts at 57 with 8-byte entries: 57 + 98*8 = 841. Data at 841? But zlib was at 1625!
# Let me check what's at 841:
print("bytes at 841:", " ".join(f"{b:02X}" for b in h[841:857]))
print("bytes at 1625:", " ".join(f"{b:02X}" for b in h[1625:1641]))
# Maybe the header is bigger. What if there's a 4-byte "CompressionBlockSize" AND the flags byte
# is elsewhere? Let me try: header = 57 + 4 = 61? 61 + 98*16 = 1617. no.
# What if NumBlocks is at 48 but there are extra fields? Let me try header=57, entries 16B,
# and the u64s are at 57+16i and 57+16i+8:
for i in range(4):
    a, b = struct.unpack_from("<QQ", h, 57 + 16*i)
    print(f"blk[{i}] @ {57+16*i}: {a} {b}")
