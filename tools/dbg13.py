import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
f.seek(339628863)
idx = f.read(165602)
# PATTERN FOUND! Look at the bytes: "00 E0 79 23 3E 14 A8 02" 
# The pattern "3E 14" appears repeatedly — 0x143E = 5182... no wait. As part of a 64-bit LE value:
# "79 23 3E 14" = 0x143E2379 = 339842937 — A VALID PAK OFFSET (near the index at 339628863)!
# So the offset field is "79 23 3E 14 ..." but there's an "00 E0" prefix.
# The bit stream: "00 E0" then "79 23 3E 14"...
# Reading LSB-first: byte0=0x00 (8 bits: 0), byte1=0xE0 (bits: 0,0,0,0,0,1,1,1)
# So after 8 zero bits, bits 8-12 = 0, bits 13,14,15 = 1,1,1
# 31-bit offset = bits 0..30. Bits 0-12 = 0 (13 bits), bits 13-15 = 1 (3 bits) -> offset so far = 0xE000
# Then byte2=0x79: bits 16-23 = 0,1,1,1,1,0,0,1 (LSB first: 79 = 0111 1001 -> LSB first: 1,0,0,1,1,1,1,0)
# Hmm wait: 0x79 = 0111 1001 binary. LSB (bit0) = 1, bit1 = 0, bit2 = 0, bit3 = 1, bit4 = 1, bit5 = 1, bit6 = 1, bit7 = 0
# So bits 16-23 = 1,0,0,1,1,1,1,0
# offset bits: [0-12]=0, [13]=1,[14]=1,[15]=1, [16]=1,[17]=0,[18]=0,[19]=1,[20]=1,[21]=1,[22]=1,[23]=0, ...
# offset = (1<<13)|(1<<14)|(1<<15)|(1<<16)|(1<<19)|(1<<20)|(1<<21)|(1<<22) = 0x2000+0x4000+0x8000+0x10000+0x80000+0x100000+0x200000+0x400000
# = 0x798000... continuing with byte3=0x23: 0x23 = 0010 0011 -> LSB first: 1,1,0,0,0,1,0,0
# bits 24-31 = 1,1,0,0,0,1,0,0
# offset bits 24-30 = 1,1,0,0,0,1,0 -> offset |= (1<<24)|(1<<25)|(1<<29) = 0x23000000
# Total offset so far (31 bits) = 0x23000000 + 0x798000 + ... let me just compute properly.
# Actually my BitReader already does this! It gave off=595189760 = 0x237C0000.
# Hmm, but the expected offset is ~339842937 = 0x143E2379.
# 0x237C0000 vs 0x143E2379 — the BYTES ARE BYTE-SWAPPED-ish! 0x143E2379 vs 0x237C0000...
# 79 23 3E 14 as LE = 0x143E2379 ✓ (the offset!). But my bit reader read "00 E0 79 23" first.
# So the entry's bits start at enc+2 (skipping "00 E0")! The "00 E0" might be the tail of the PREVIOUS entry!
# enc=165476: bytes "00 E0 79 23 3E 14 A8 02 00 00 00 00 00 E0 56 26 3E 14 51 00"
# If entry starts at 165478: offset = "79 23 3E 14 ..." 
# But wait, the offset is 31 BITS not 4 bytes. Reading 31 bits LSB-first from "79 23 3E 14 A8 02":
# 0x79=0111 1001, LSB first: 1,0,0,1,1,1,1,0
# 0x23=0010 0011, LSB first: 1,1,0,0,0,1,0,0
# 0x3E=0011 1110, LSB first: 0,1,1,1,1,1,0,0
# 0x14=0001 0100, LSB first: 0,0,1,0,1,0,0,0
# bits: [1,0,0,1,1,1,1,0, 1,1,0,0,0,1,0,0, 0,1,1,1,1,1,0,0, 0,0,1,0,1,0,0,...]
# 31-bit value = bit0=1(1) + bit4=1(16) + bit5=1(32)+bit6=1(64) + bit8=1(256)+bit9=1(512) + bit13=1(8192)
# + bit17..21 = 1<<17? Let me just trust the BitReader but start at 165478.
class BR:
    def __init__(s, d, p):
        s.d = d; s.p = p; s.v = 0; s.b = 0
    def read(s, n):
        while s.b < n:
            byte = s.d[s.p]; s.p += 1
            s.v |= byte << s.b; s.b += 8
        r = s.v & ((1 << n) - 1); s.v >>= n; s.b -= n
        return r

for start in (165476, 165477, 165478):
    br = BR(idx, start)
    off = br.read(31); same = br.read(1)
    us = cs = None
    if not same:
        us = br.read(32); cs = br.read(32)
    comp = br.read(6); hb = br.read(1)
    print(f"start={start}: off={off} ({hex(off)}) same={same} us={us} cs={cs} comp={comp} hb={hb}")
