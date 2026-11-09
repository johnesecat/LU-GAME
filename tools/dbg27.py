import struct, zlib
data = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb").read()
off = 156436480
h = data[off:off+1700]
# Pattern: "00 00 00 00 XX XX 00 00" repeated — u64 at 59 = 8072192 = 0x7B2C00.
# Wait: u64@59 = 8072192 = 0x7B2C00. Hmm, that's 11371 << 8? No: 0x7B2C00 = 8072192.
# Actually 11371 = 0x2C7B. And 0x7B2C00... the bytes at 59-66 are "2C 7B 00 00 00 00 00 00" = 0x7B2C = 11371!
# Wait the printout says u64@59 = 8072192. Let me recheck: bytes[59..66]:
# [59]=2C [60]=7B [61]=00 [62]=00 [63]=00 [64]=00 [65]=00 [66]=00
# LE u64 = 0x0000000000007B2C = 11371. But the printout says 8072192?!
# Oh! The printout above used h = data[off:off+400] in dbg26 but here I sliced differently.
# In dbg26, h was data[off:off+400] and u64@59 gave 8072192. But bytes 56-63 = "00 00 00 00 2C 7B 00 00"
# so u64@59 = bytes 59-66 = "2C 7B 00 00 00 00 00 00"?? no wait [64]=00 [65]=00 [66]=00 [67]=00.
# Hmm the dump shows [64] row = "00 00 00 00 2C 7B 00 00" meaning bytes 64-71.
# So [59]=2C? No! Row [56] = bytes 56-63 = "00 00 00 00 2C 7B 00 00". So [56]=00 [57]=00 [58]=00 [59]=00 [60]=2C [61]=7B [62]=00 [63]=00.
# I misindexed! u64@59 = bytes 59-66 = "00 2C 7B 00 00 00 00 00" = 0x7B2C00 = 8072192. ✓ matches printout.
# So the actual values: u32 at 60 = 0x7B2C = 11371. u32 at 68 = 11371. u32 at 76 = 0xEEC9 = 61129.
# Pattern per 8 bytes: "00 00 00 00 [u32 value]" — i.e., u64 at 56, 64, 72... where the u64 = value<<32?
# u64@56 = bytes 56-63 = "00 00 00 00 2C 7B 00 00" = 0x00007B2C00000000 = 134868873949184?? 
# Hmm no: LE u64 of [00,00,00,00,2C,7B,00,00] = 0x00007B2C00000000. That's huge.
# BUT if I read u64 at 60: bytes 60-67 = "2C 7B 00 00 00 00 00 00" = 0x7B2C = 11371 ✓
# So values are u64 at 60, 68, 76, ... spaced 8. Table starts at 60? Then 60 + 98*8 = 844.
# But data starts at 1625 = 57 + 98*16. Contradiction!
# UNLESS the table has TWO u64 per entry: (start, end) at 60 and 68? entry0: start=11371, end=11371?
# Hmm both equal. What if entry = (u64 start, u64 end) where start/end are RELATIVE offsets
# into the compressed data, and block0 = [0, 11371)? Then entry0 = (0, 11371)?
# But u64@60 = 11371 and u64@68 = 11371. If entry0 = (u64@60, u64@68) = (11371, 11371) — no.
# What if the table starts at 56 with entries (u64 start, u64 end):
# entry0 = (u64@56, u64@64) = (0x7B2C00000000, 0x7B2C00000000)?? no.
# Let me try yet another interpretation: entries are (u32 start, u32 end) at 60:
# entry0: start = u32@60 = 11371, end = u32@64 = 0?? bytes 64-67 = "00 00 00 00" = 0.
# Hmm.
# OK radical idea: what if the block table entries are (u64 start, u64 end) where the u64s
# are at 56+16*i and 56+16*i+8, and the values are:
#   u64@56 = 0x00007B2C00000000?? Let me just print u64 at 56, 72, 88 (16-byte spacing):
for i in range(56, 56+16*6, 16):
    a, b = struct.unpack_from("<QQ", h, i)
    print(f"entry@{i}: start={a} end={b} len={b-a}")
print()
# and u32 pairs at 60 with 16-byte spacing:
for i in range(60, 60+16*6, 16):
    a, b = struct.unpack_from("<II", h, i)
    print(f"u32pair@{i}: {a} {b}")
