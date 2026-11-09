import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
# CLEAR NOW! Header at 2048:
# 2048-2055: offset = 00 00 00 00 00 00 00 00 = 0
# 2056-2063: size = 0F 03 00 00 00 00 00 00 = 783
# 2064-2071: usize = 783
# 2072-2075: comp = 00 00 00 00 = 0
# 2076-2095: hash (20B): 94 9E 95 CF CD A9 97 88 90 F6 94 37 7D A2 4B D9 FF 6D 70 90
# 2096-2099: blocks = 00 00 00 00 = 0
# 2100: enc = 00
# 2101: data starts = C1 83 2A 9E F9 FF FF FF ✓✓✓
# So header is at 2048, data at 2101. Header size = 53. ✓
# So the walk rule: header(53) + size. The zero-size entries ARE real (deleted files).
# My earlier walk failed because at 2004 I read enc=15 and then jumped to 2057 (2004+53).
# But the real header is at 2048, not 2057! 2004+53 = 2057 ≠ 2048.
# So the zero-size entries are NOT 53 bytes each. Let me figure out their size:
# zero entries at 1156, 1209, 1262, ... 2004 (53 apart) then real header at 2048.
# 2004 + 44 = 2048. So the LAST zero entry is 44 bytes? Or the zero entries are variable?
# Hmm: 1156, 1209, 1262, 1315, 1368, 1421, 1474, 1527, 1580, 1633, 1686, 1739, 1792, 1845, 1898, 1951, 2004
# All 53 apart. 2004 + 53 = 2057. But header at 2048. So the entry at 2004 is only 44 bytes!
# UNLESS the entry at 2004 is NOT all-zero. From my walk: "2004: off=0 size=0 usize=0 comp=0 blocks=0 enc=15"
# enc=15?! That's odd. Let me look at 2004..2057.
f.seek(2004)
d = f.read(53)
print(" ".join(f"{b:02X}" for b in d))
# Also: maybe zero-size entries are actually 4-byte entries (just a "deleted" flag)?
# 1156 + 4 = 1160, but next zero at 1209 (53 later). So no.
# What if the zero entries are 53 bytes but the LAST one before a real file is shorter?
# Actually maybe the zero region 1156..2048 is ONE file's data (a file of 892 zero bytes)!
# The header at 1099... no wait. Let me reconsider: header at 1099? We showed hdr@1099 is invalid.
# What if there's a header at 1103 (1156-53)? The zero region starts at 1156.
# If a file's data is 1156..2048 (892 zero bytes), its header is at 1103.
# hdr@1103: offset 1103-1110, size 1111-1118 = ? Let me check.
f.seek(1103)
h = f.read(53)
o, s, u = struct.unpack_from("<qqq", h, 0)
c = struct.unpack_from("<i", h, 24)[0]
b = struct.unpack_from("<I", h, 48)[0]
e = h[52]
print("hdr@1103:", "off=", o, "size=", s, "usize=", u, "comp=", c, "blocks=", b, "enc=", e)
