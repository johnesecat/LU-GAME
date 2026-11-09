import struct, zlib
data = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb").read()
off = 156436480
h = data[off:off+400]
# bytes 48-51: "62 00 00 00" = 98 blocks
# byte 52: 0x89 = 10001001b — this is the "flags" byte: bit0=encrypted? bits: 
#   In UE5 FPakEntry serialization: after hash comes:
#   uint32 NumBlocks, uint8 flags (bit0 encrypted, bit1 offset32, bit2 unsize32, bit3 size32),
#   uint32 CompressionBlockSize, then block table (u64 start, u64 end per block)
# byte 52 = 0x89 = 1000 1001: bit0=1 (encrypted), bit3=1, bit7=1
# Hmm but encrypted=1 would mean AES. But zlib data at data_start decompresses fine...
# Actually wait: byte 52=0x89. Let me reconsider: maybe it's:
#   [48-51] NumBlocks=98, [52] flags=0x89, [53-56] cbs=6?? "59 06 00 00"=1625
# cbs=1625? That's odd. But data_start = off+57+98*16 = off+1625! So cbs is NOT at 53.
# Actually "59 06 00 00" = 1625 = the size of the header+block table! No wait...
# Let me re-read: bytes 48-56 = "62 00 00 00 59 06 00 00 00"
# [48-51]=98 (NumBlocks), [52]=0x59?? no: [52]=0x59? Let me index carefully:
# h[48]=0x62 h[49]=0x00 h[50]=0x00 h[51]=0x00 -> NumBlocks=98
# h[52]=0x59 h[53]=0x06 h[54]=0x00 h[55]=0x00 -> if u32: 0x659=1625
# h[56]=0x00
# So [52-55] = 1625 = CompressionBlockSize? No — 1625 is too small for a block size.
# BUT: 57 + 98*16 = 57 + 1568 = 1625! So [52-55] is NOT cbs.
# Hmm, what if the layout is: NumBlocks(4) at 48, then flags byte at 52, then cbs(4) at 53?
# h[52]=0x59=89, h[53..56]="06 00 00 00"=6?? cbs=6? No.
# What if: NumBlocks(4) at 48, cbs(4) at 52 (=1625?? no)...
# Let me try: the block table starts at 57 and each entry is 16 bytes (u64 start, u64 end).
# First block entry bytes 57-72: "00 00 00 2C 7B 00 00 00 00 00 00 2C 7B 00 00 00"
# As u64 LE: start = 0x7B2C00000000?? = 134,868,873,949,184. Way too big.
# As u32 pairs: (0x2C000000, 0x7B) = (738197504, 123). Hmm.
# What if block entries are (u32 start, u32 end)? Then: start=0x2C000000?? no.
# What if the bytes are: "00 00 00 2C" = 0x2C000000?? LE u32 of "00 00 00 2C" = 0x2C000000 = 738197504.
# Hmm. What if block entries are (u64 start, u64 end) but with start/end RELATIVE and SMALL?
# "00 00 00 2C 7B 00 00 00" as u64 LE = 0x00007B2C00000000. As u64 BE = 0x0000002C7B000000.
# Neither is small.
# WAIT. What if the block table entries are 8 bytes each: (u32 start, u32 end)?
# bytes 57-64: "00 00 00 2C 7B 00 00 00" -> start=0x2C000000?? no. LE u32 "00 00 00 2C" = 0x2C000000.
# Hmm what about reading from 56 instead? h[56]=0x00, h[57]=0x00, h[58]=0x00, h[59]=0x2C...
# Let me try block table at 56: bytes 56-71: "00 00 00 2C 7B 00 00 00 00 00 00 2C 7B 00 00 00"
# u64 at 56 = 0x00007B2C00000000. Still weird.
# What if entries are (u32 compressedSize, u32 uncompressedSize) per block?
# bytes 57-64: "00 00 00 2C" = 0x2C000000?? LE = 738197504. no.
# Hmm, let me look at the pattern: "00 00 00 2C 7B 00 00 00 | 00 00 00 2C 7B 00 00 00 | 00 00 00 C9 EE 00 00 00"
# 0x2C7B = 11371, 0xEEC9 = 61129. These look like BLOCK SIZES!
# If each entry is 8 bytes: (u32 something, u32 size)? "00 00 00 2C" then "7B 00 00 00"?
# OR the entries are 8 bytes: u64 LE where value = 0x7B2C00000000?? 
# OR: entries are (u32 start, u32 end) where start/end are byte offsets relative to data start:
#   entry0: start=0x2C000000?? no.
# What if it's (u32 end, u32 start)?? 
# Let me try: what if each block entry is 8 bytes = (u32 compressed_block_size, u32 uncompressed_block_size)?
# entry0: "00 00 00 2C" = 0x2C000000?? no. LE u32 of bytes "00 00 00 2C" = 0x2C000000 = 738197504. no.
# Hmm, what if I misread the byte order? Let me print bytes 56-100 carefully.
print("bytes 56-120:")
for i in range(56, 120, 8):
    print(f"  [{i:3d}]", " ".join(f"{b:02X}" for b in h[i:i+8]))
# Pattern: "00 00 00 2C 7B 00 00 00" repeated, then "00 00 00 C9 EE 00 00 00"
# If u32 at 59: "2C 7B 00 00" = 0x7B2C = 11371. And u32 at 67: "2C 7B 00 00" = 11371.
# And u32 at 75: "C9 EE 00 00" = 0xEEC9 = 61129.
# So the values 11371, 11371, 61129 are at offsets 59, 67, 75 — spaced 8 apart!
# So each block entry is 8 bytes with the value at +3? That means entries start at 56 with a 
# 3-byte prefix? OR entries are (u32 pad, u32 value)? 
# bytes 56-63: "00 00 00 2C 7B 00 00 00" — if entry = (u32 x, u32 y): x=0x2C000000, y=0x7B.
# Hmm no. What if entries are u64 LE: 0x00007B2C00000000 = 134868873949184.
# What if entries are u64 BE: 0x0000002C7B000000 = 134868848640.
# What if the block table starts at 59 and entries are 8 bytes: (u32 start, u32 end)?
# entry0 at 59: start = "2C 7B 00 00" = 11371, end = "00 00 00 2C"?? = 0x2C000000. no.
# What if entries are (u32 end, u32 start)? end=11371, start=0x2C000000. no.
# OK here's the thing: 11371 and 61129 — if these are block END offsets (cumulative), then
# block0 = 0..11371, block1 = 11371..22742, block2 = 22742..61129?? But block2 should be
# 65536-cbs... hmm 61129 < 65536. And cbs might be 65536.
# Actually! What if the table is (u64 start, u64 end) but stored as u32 pairs with the LOW
# 32 bits only? I.e., entries are (u32 start, u32 end) = (11371, 11371)?? no.
# Let me just try: block table at 59, entries of 8 bytes (u32 start, u32 end):
# entry0: start=11371, end=11371?? Both same. Weird.
# What if it's (u32 compressedSize, u32 uncompressedSize) per block at 59?
# entry0: csize=11371, usize=11371?? Both same — but compression should shrink!
# Hmm, unless... wait. Let me reconsider. What if the table is at 57 and entries are 8 bytes:
# (u32 start, u32 end) where start/end are relative to the DATA start:
# entry0 bytes 57-64: "00 00 00 2C 7B 00 00 00" -> start = LE u32 at 57 = 0x2C000000?? 
# I keep messing up. LE u32 of bytes [00,00,00,2C] = 0x2C000000. LE u32 of [2C,7B,00,00] = 0x00007B2C = 11371.
# So the value 11371 is at offset 59 (bytes 59-62). The next 11371 is at 67. The 61129 at 75.
# Spacing = 8. So table entries are 8 bytes, values at +3 within each entry?? That's bizarre
# UNLESS the entries are u64 and I should read the u64 at 59: bytes 59-66 = "2C 7B 00 00 00 00 00 2C"?? 
# no wait, bytes 59-66 = [59]=2C [60]=7B [61]=00 [62]=00 [63]=00 [64]=00 [65]=00 [66]=00 -> u64 = 0x7B2C = 11371!
# YES! u64 LE at 59 = 11371. And u64 at 67 = 11371. And u64 at 75 = 61129.
# So the block table starts at 59, entries are u64, spaced 8 bytes. But then what are bytes 57-58?
# bytes 57,58 = 00 00. And the first entry's u64 at 59 = 11371.
# Hmm, but that means the table starts at 59, not 57. What's at 57-58? "00 00" — padding?
# OR the table starts at 57 and entries are u64 but the first entry is at 57+2=59?
# Actually maybe the header is: NumBlocks(4)@48, flags(1)@52, cbs(4)@53, then table@57.
# cbs = LE u32 at 53 = "06 00 00 00" = 6?? cbs=6? No...
# wait h[53]=0x06? From the dump: [48]=62 [49]=00 [50]=00 [51]=00 [52]=59 [53]=06 [54]=00 [55]=00 [56]=00
# Hmm h[52]=0x59=89, h[53]=0x06. So cbs at 53 = 0x00000006 = 6? That can't be a block size.
# UNLESS: [52] is a flags byte (0x59 = 0101 1001: bit0=1 encrypted? bit3=1, bit4=1, bit6=1)
# and cbs is at 53-56 = "06 00 00 00" = 6?? 
# OR: [52-55] = "59 06 00 00" = 0x659 = 1625 = CompressionBlockSize? 1625 is odd but possible?
# Hmm, but 57 + 98*16 = 1625. Coincidence? If the table is 98 entries of 8 bytes starting at 57:
# 57 + 98*8 = 841. Data would start at 841. But we found zlib data at 1625!
# If table is 98 entries of 16 bytes starting at 57: 57 + 1568 = 1625 ✓!!
# So entries ARE 16 bytes. But then u64 at 59 = 11371 doesn't fit a 16-byte entry at 57.
# UNLESS entries are (u64 start, u64 end) at 57: entry0 = u64@57, u64@65.
# u64@57 = bytes 57-64 = "00 00 00 2C 7B 00 00 00" = 0x00007B2C00000000?? 
# Hmm wait: LE u64 of [00,00,00,2C,7B,00,00,00] = 0x00007B2C00000000. That's 134 trillion. no.
# What if entries are (u64 start, u64 end) but I have the wrong start? Let me try table at 59:
# entry0: u64@59 = 11371 (start), u64@67 = 11371 (end)?? start==end? no.
# What if entry = (u64 start, u64 end) at 59: start=11371, end=11371. Block of length 0? no.
# Hmm, what if it's (u64 end_of_block0, u64 end_of_block1, ...)? i.e., cumulative ends?
# u64@59=11371, u64@67=11371, u64@75=61129. If these are cumulative ends: block0=0..11371,
# block1=11371..11371 (empty?), block2=11371..61129. Weird.
# What if they're (u32 csize, u32 usize) pairs at 59? entry0: csize=11371, usize=11371.
# For zlib, csize != usize usually. Unless... hmm.
# Let me look at more entries to find the pattern.
print()
print("u64 values at 59, 67, 75, ...:")
for i in range(59, 59+8*10, 8):
    v, = struct.unpack_from("<Q", h, i)
    print(f"  u64@{i} = {v}")
