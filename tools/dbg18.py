import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
f.seek(339628863)
idx = f.read(165602)
# The file at offset 0 (data at 53) is BreakOutFloat2Components — but FDI's first entry is
# 'Lerp_Multiple_Float.uasset' with enc=120. So FDI order != pak storage order. Fine.
# The FDI enc values point to entries in the encoded region. The entry at enc=120 should describe
# a file. Let me look at bytes 120-140 again: "00 00 00 00 00 E0 5C 03 00 00 F3 00 00 00 00 00 00 E0 00 08"
# Hmm wait, that was from the earlier dump at position 120 of the INDEX (which starts at 339628863).
# Actually from dbg12: "bytes at 120: 00 00 00 00 00 E0 5C 03 00 00 F3 00 00 00 00 00 00 E0 00 08"
# If the entry starts at 120: 31 bits from "00 00 00 00 00" = 0, then bit31 from E0's bit7=1 -> same=1
# then 32-bit size from "5C 03 00 00"?? No wait — after 31+1=32 bits (bytes 120-123 = "00 00 00 00"),
# bit31 comes from byte 124 (0x00)? I'm confusing myself.
# Let me carefully define: BitReader reads bits LSB-first, byte by byte.
# Entry at 120: bytes b0=0x00 b1=0x00 b2=0x00 b3=0x00 b4=0x00 b5=0xE0 b6=0x5C b7=0x03 b8=0x00...
# 31-bit offset: bits 0-30. bits 0-7=b0=0, bits 8-15=b1=0, bits 16-23=b2=0, bits 24-30 = b3 low 7 bits = 0
# -> offset = 0
# bit31 = b3 bit7 = 0 -> same=0
# Then usize 32 bits: bits 32-63 = b4(0x00), b5(0xE0), b6(0x5C), b7(0x03)
# = 0x00 | 0xE0<<8 | 0x5C<<16 | 0x03<<24 = 0x035CE000 = 56418304. That's what we got before!
# 56418304 is way too big. BUT: 0x035CE000... hmm what if it's actually [usize][csize] where
# usize = 0x035CE000?? No.
# What if the sizes are 31 bits + 1 flag too? Or what if there's a "compression method" BEFORE sizes?
# Let me try: [31 offset][1 same][6 comp][1 hb][32 size]...
# bits 32-37 = comp = b4 low 6 bits = 0
# bit 38 = hb = b4 bit6 = 0
# bit 39 = ? 
# Hmm.
# NEW IDEA: What if the FDI enc values are relative to the START OF THE ENCODED REGION (110)?
# Then entry for enc=120 is at index position 110+120 = 230.
print("bytes at 230:", " ".join(f"{b:02X}" for b in idx[230:250]))
class BR:
    def __init__(s, d, p):
        s.d = d; s.p = p; s.v = 0; s.b = 0
    def read(s, n):
        while s.b < n:
            byte = s.d[s.p]; s.p += 1
            s.v |= byte << s.b; s.b += 8
        r = s.v & ((1 << n) - 1); s.v >>= n; s.b -= n
        return r
br = BR(idx, 230)
off = br.read(31); same = br.read(1)
print("off=", off, "same=", same)
if not same:
    us = br.read(32); cs = br.read(32)
    print("us=", us, "cs=", cs)
