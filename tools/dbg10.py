import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
# NOW I see it! Look at 1140: "0B 00 00 00 00 00 00 00 00 00 00 00 C1 83 2A 9E"
# and 1124: 16-byte GUID "6E DB 1D 2C FC C9 6B 40 A1 41 41 1D 2A 12 82 7C"
# This is the END of the .uexp file! UE uexp files end with:
#   [GUID 16B][serialSize 8B][tag 4B]  <- actually the uexp trailer is:
#   ...data... [u64 serialSize][u32 0][u32 tag]? 
# Hmm: 1124-1139 GUID, 1140-1147 = 0B 00 00 00 00 00 00 00 = 11 (serial size?), 
# 1148-1151 = 00 00 00 00, 1152-1155 = C1 83 2A 9E (tag!)
# So the uexp ends at 1156. The uexp data = 913..1156 = 243 bytes ✓✓✓ MATCHES the header size=243!
# So the uexp at 913 IS 243 bytes and ends at 1156. The C1 83 2A 9E at 1152 is the uexp's trailing tag.
# Then the next header is at 1156 (all zeros = size 0 entry). The zero entries continue to 2048.
# 2048-1156 = 892. 892 / 53 = 16.83 — NOT integer. So zero-size entries aren't 53 bytes.
# UNLESS zero-size entries have NO hash (20 bytes)! A zero-size entry might serialize as:
# [offset 8][size 8][usize 8][comp 4][blocks 4][enc 1] = 33 bytes? 892/33 = 27.03. No.
# What about [flags] only? In UE5, when the index is encoded, files may have NO inline header at all!
# The inline header is only present for files NOT in the encoded index... 
# Actually in UE5.1+: FPakEntry headers are stored inline ONLY when the pak uses the encoded index.
# The encoded index stores a BIT for each file: 1 = has inline header, 0 = no header (data only).
# Hmm, but then how do we know sizes?
# WAIT. Let me reconsider. What if the zero region 1156..2048 is a single FILE's data (892 zero bytes)?
# Its header would be at 1103. We parsed hdr@1103 as off=0 size=0 — but if the header is at 1103
# and the file is 892 bytes, size should be 892. Unless the header at 1103 is:
# Let me look at 1103..1156: from the dump, 1103 is inside "00 00 00 00 00 00 00 09" region...
# 1092 row: "00 00 00 00 00 00 00 09" -> 1092-1098 are 00, 1099=09
# So at 1103: all zeros until 1124 (GUID). A header at 1103 would be:
#   offset(1103-1110)=0, size(1111-1118)=0, usize(1119-1126)= 6E DB 1D 2C... garbage.
# Not valid. So the zero region is NOT a file with a header at 1103.
# CONCLUSION: The zero region must be multiple zero-size entries OR padding.
# Let me check: are there other all-zero regions in the pak? And what precedes/follows them?
# Actually, let me look at this from the ENCODED INDEX angle again. The FDI gives (name, enc_offset).
# The enc_offset points into the index where the entry's bits are. My bit-parse gave garbage, but
# maybe I had the wrong base. The encoded entries start right after "encodedEntriesCount" at index+110.
# The first FDI file has enc=120. If entries start at 110, then enc=120 means 10 bytes in.
# Hmm, but maybe enc is relative to the START OF THE INDEX (339628863), so absolute = 339628863+120.
# That's what I did (idx[120]). Garbage result.
# What if the bit order is MSB-first within each 32-bit value but LSB-first across bytes? 
# UE's FBitReader reads bits LSB-first from bytes. My implementation does that. 
# Let me try parsing with the assumption that values are read MSB-first (big-endian bit order):
class BRMSB:
    def __init__(s, d, p):
        s.d = d; s.p = p; s.v = 0; s.b = 0
    def read(s, n):
        while s.b < n:
            byte = s.d[s.p]; s.p += 1
            s.v = (s.v << 8) | byte; s.b += 8
        r = (s.v >> (s.b - n)) & ((1 << n) - 1)
        s.b -= n; s.v &= (1 << s.b) - 1
        return r

f.seek(339628863)
idx = f.read(165602)
# Try entry for the LAST file (enc=165476) with MSB-first
br = BRMSB(idx, 165476)
off = br.read(31); same = br.read(1)
print("MSB enc=165476: off=", off, "same=", same)
if not same:
    us = br.read(32); cs = br.read(32)
    print("  us=", us, "cs=", cs)
comp = br.read(6); hb = br.read(1)
print("  comp=", comp, "hb=", hb)
