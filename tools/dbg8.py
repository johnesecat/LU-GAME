import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
# The dump of 2004..2056 shows: 52 zeros then 0F at 2056. So the "entry at 2004" is 52 zero bytes,
# and 0F 03 at 2056 is the size field of the NEXT header (at 2048)!
# So the zero region 1156..2048 = 892 bytes. If it's one file's data, header at 1103 (invalid parse).
# What if the zero region is the data of the file whose header is at 1099? hdr@1099 gave off=9 size=0.
# Hmm, off=9?? "09 00 00 00 00 00 00 00" at 1099. That 09 might be part of the previous uexp's trailer!
# UE uexp trailer: [C1 83 2A 9E][u32 0][u64 serialSize]. The uexp at 913..1156:
# ...C1 83 2A 9E at 1152, then 1156-1159 = 00 00 00 00, 1160-1167 = serial size.
# But the zero region starts at 1156. So the uexp ends at 1152+4+8 = 1164? 
# Actually the uexp trailer is: package tag (4) + 0 (4) + serial size (8) = 16 bytes at the END.
# If C1 83 2A 9E is at 1152, the trailer is 1152..1167, so the uexp data ends at 1168.
# But the header at 860 said size=243: 913+243 = 1156. The trailer would be at 1140..1156 with tag at 1140.
# But we found the tag at 1152! So the uexp is actually 913..1168 (255 bytes), not 243.
# 255 - 243 = 12. Hmm.
# OR the header at 860 has size=243 but that's the COMPRESSED size and there's a 12-byte discrepancy...
# You know what, let me try yet another interpretation: maybe the inline header is 57 bytes (with cbs).
# Then: entry0 hdr at 0..56, data 57..864? But C1 83 2A 9E is at 53! So no.
# Let me try: header = 53 bytes, but files are stored with 4-byte alignment padding AFTER the header?
# entry0: hdr 0..52, data 53..860 (807 bytes) ✓ (C1 at 53 ✓)
# entry1: hdr 860..912, data 913..? size 243 -> 1156. But next real header is at 2048.
# The gap 1156..2048 = 892 bytes of zeros. If entry1's data is 913..1156 (243B), then entries at
# 1156, 1209, ... are zero-size entries (53B each) until 2004, then 2048.
# 2004 + 44 = 2048. The last zero "entry" would be 44 bytes. OR the zero entries are 53B and the
# last one at 2004 is followed by 2048-2057 = -9... 
# Count: from 1156, entries at 1156+53k. 2048-1156 = 892. 892/53 = 16.83. Not integer!
# So the zero region is NOT 53-byte entries. It must be ONE file's data (892 zero bytes) OR padding.
# If it's a file's data, its header is at 1156-53 = 1103. hdr@1103 parse gave garbage because the
# "header" is all zeros except... wait the dump showed 52 zeros + 0F. At 1103 the bytes are all zero
# (from the 1090 dump: 1103 is in the zero region before 1124's hash bytes).
# Hmm, hdr@1103: off=0 size=0 — but then where do the hash bytes at 1125-1144 come from?
# They'd be INSIDE the zero-file's data? No, they're non-zero!
# Let me dump 1099..1160 again very carefully. From dbg4 output:
# 1098: 00 09 00 00 00 00 00 00  -> 1098=00, 1099=09, 1100-1105=00
# 1106: 00 00 00 00 00 00 00 00
# 1114: 00 00 00 00 00 00 00 00
# 1122: 00 00 6E DB 1D 2C FC C9  -> 1122=00, 1123=00, 1124=6E
# 1130: 6B 40 A1 41 41 1D 2A 12
# 1138: 82 7C 0B 00 00 00 00 00
# 1146: 00 00 00 00 00 00 C1 83  -> 1152=C1
# So non-zero bytes: 1099=09, 1124-1145 = 6E DB 1D 2C FC C9 6B 40 A1 41 41 1D 2A 12 82 7C 0B 00 00 00 00 00
# Wait 1138 row: 82 7C 0B 00 00 00 00 00 -> 1138=82, 1139=7C, 1140=0B, 1141-1145=00
# So the "hash-like" bytes are 1124..1139 (16 bytes): 6E DB 1D 2C FC C9 6B 40 A1 41 41 1D 2A 12 82 7C
# then 0B at 1140, then zeros, then C1 at 1152.
# Structure: [1099: 09][1100-1123: zeros][1124-1139: 16 bytes][1140: 0B][1141-1151: zeros][1152: C1 83 2A 9E]
# If header at 1099: offset=09?? A 53-byte header 1099..1151 would be:
#   offset(1099-1106) = 09 00 00 00 00 00 00 00 = 9
#   size(1107-1114) = 0
#   usize(1115-1122) = 0
#   comp(1123-1126) = 00 6E DB 1D = garbage
# Not valid. What if header at 1100? offset=0, size(1108-1115)=0, usize(1116-1123)=0, comp(1124-1127)=6E DB 1D 2C garbage.
# What if the 16 bytes at 1124-1139 are a GUID (not a header hash)? And this is the uexp TRAILER region?
# UE uexp trailer = [tag 4B][0 4B][serialSize 8B] = 16 bytes! 
# If the uexp's trailer is at 1124..1139: tag would be at 1124 = 6E DB 1D 2C? Not C1 83 2A 9E.
# Hmm. But wait — the uexp at 913 with size 243 ends at 1156. Its LAST 16 bytes (1140..1155) would be
# the trailer: 0B 00 00 00 00 00 00 00 | 00 00 00 00 00 00 C1 83?? No, trailer = tag+0+size.
# I wonder if the uexp trailer is: [serialSize 8B][tag 4B][0 4B]? Then 1140..1155: 0B 00...00 C1 83 2A 9E?
# 0B = 11? serial size 11? Hmm.
# Actually the REAL UE uexp trailer format: the last 16 bytes are
#   [u32: 0][u32: 0][u64: serialSize]?? No.
# Let me just check the uexp at 913: its content is "Enter a float 2 vector..." (a comment property).
# The file is 243 bytes: 913..1156. The last bytes 1140..1156: 0B 00 00 00 00 00 00 00 00 00 00 00 00 00 C1 83
# Hmm 0B could be part of data.
# NEW HYPOTHESIS: the 16 bytes 1124-1139 are the pak entry's inline hash, meaning the header is at
# 1124-28 = 1096? comp at 1092-1095? Let me try header at 1096:
f.seek(1096)
h = f.read(53)
o, s, u = struct.unpack_from("<qqq", h, 0)
c = struct.unpack_from("<i", h, 24)[0]
b = struct.unpack_from("<I", h, 48)[0]
e = h[52]
print("hdr@1096:", "off=", o, "size=", s, "usize=", u, "comp=", c, "blocks=", b, "enc=", e)
print(" ".join(f"{x:02X}" for x in h))
