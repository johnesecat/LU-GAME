import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
# Now clear: C1 83 2A 9E at 1152-1155.
# Header for this uasset: 1152-53 = 1099. Header bytes 1099..1151:
# 1099-1106: 00 00 00 00 00 00 00 00 (offset=0)
# 1107-1114: 00 00 00 00 00 00 00 00 -> wait from dump: 1106 row = "00 00 00 00 00 00 00 00" (1106-1113)
# Let me get exact: header at 1099 spans 1099..1151 (53 bytes).
# 1099-1106 (offset 8B), 1107-1114 (size 8B), 1115-1122 (usize 8B), 1123-1126 (comp 4B),
# 1127-1146 (hash 20B), 1147-1150 (blocks 4B), 1151 (enc 1B)
# From dump: 1098 row "00 09 00 00 00 00 00 00" covers 1098-1105. So 1099-1105 = "09 00 00 00 00 00 00" + 1106=00
# offset = bytes 1099..1106 = 09 00 00 00 00 00 00 00 = 9?? Hmm.
# 1107-1114 = from rows: 1106-1113 = "00 00 00 00 00 00 00 00", 1114 = 00. So size = 0?
# This is a mess. Let me just read the 53 bytes at 1099 directly.
f.seek(1099)
h = f.read(53)
o, s, u = struct.unpack_from("<qqq", h, 0)
c = struct.unpack_from("<i", h, 24)[0]
b = struct.unpack_from("<I", h, 48)[0]
e = h[52]
print("hdr@1099:", "off=", o, "size=", s, "usize=", u, "comp=", c, "blocks=", b, "enc=", e)
print(" ".join(f"{x:02X}" for x in h))
