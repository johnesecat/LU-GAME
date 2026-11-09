import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
f.seek(339628863)
idx = f.read(165602)
# Progress! enc=165476: off=339616633 ✓ valid, us=680 ✓ plausible, but cs=3758096384 garbage.
# The issue: after reading 31+1+32 = 64 bits, the next 32 bits gave garbage. 
# "A8 02 00 00 00 00 00 00" — wait, maybe after the 32-bit size there's ANOTHER 32-bit size but
# the bytes are "00 00 00 00" = 0? cs=0? But my parse gave 3758096384 = 0xE0000000.
# 0xE0000000 — the "00 E0" pattern again! The bit reader is consuming bits from "00 E0" bytes.
# AH WAIT. I bet the entries are BYTE-ALIGNED! Each encoded entry starts on a byte boundary.
# The "00 E0" prefix is PADDING from the previous entry!
# Look: enc=165476, bytes "00 E0 79 23 3E 14 A8 02 00 00 00 00 00 E0 56 26..."
# If the entry starts at 165478 (byte-aligned after "00 E0"), then:
#   31 bits offset from "79 23 3E" + 1 bit from "14" -> offset=339616633, flag=0
#   Then 32 bits size from "A8 02 00 00" = 680
#   Then 32 bits from "00 00 00 00" = 0?? 
# Hmm, but if flag=0 means "same size", we'd only read ONE 32-bit value (680), then:
#   comp 6 bits from byte 12 (0x00) = 0
#   hb 1 bit = 0
#   enc 1 bit = 0
#   cbs 32 bits from "E0 56 26 3E" = 0x3E2656E0?? garbage!
# Unless cbs is only present when blocks>0. Then after enc bit, the entry ENDS.
# Next entry starts at... the next byte boundary? The remaining bits in byte 12 are 0.
# So next entry at byte 13 = "E0 56 26 3E 14 51 00" — but that starts with E0 again!
# Hmm, "00 E0" appears before "79 23 3E 14" and "E0 56 26 3E 14" — the pattern "3E 14" = high bytes
# of pak offsets (0x143E....). So entries are: [some bits][offset containing 3E 14]...
# The "E0" bytes might be part of the previous entry's blockSize or flags.
# Let me try assuming entries are byte-aligned and the format per entry is:
#   [31-bit offset][1-bit flag] then if flag: [32-bit size] else [32-bit usize][32-bit csize]
#   [6-bit comp][1-bit hasBlocks] then if hasBlocks: [32-bit blocks] [per-block 64-bit]
#   [1-bit encrypted][32-bit blockSize]
# With flag=0 meaning same-size. Entry at 165478:
#   offset=339616633, flag=0 (same), size=680, comp=0, hb=0, enc=0, cbs=0
#   Total bits: 32+32+6+1+1+32 = 104 bits = 13 bytes. Entry occupies 165478..165491.
#   Bytes 165478-165490: "79 23 3E 14 A8 02 00 00 00 00 00 00 00" (13 bytes) ✓
#   Next entry at 165491: "E0 56 26 3E 14 51 00 00 00 00 00 00 00" 
#   offset from "E0 56 26 3E 14": 31 bits LSB-first from E0=1110 0000: bits 0-4=0, bit5=1,bit6=1,bit7=1
#   0x56=0101 0110: bits 8=0,9=1,10=1,11=0,12=1,13=1,14=0,15=1
#   offset = (1<<5)|(1<<6)|(1<<7)|(1<<9)|(1<<10)|(1<<12)|(1<<13)|(1<<15)|... 
#   This is getting complicated. Let me just implement byte-aligned parsing and validate against
#   known file sizes. The .uplugin files are small text files — I can verify by extracting.
class BR:
    def __init__(s, d, p):
        s.d = d; s.p = p; s.v = 0; s.b = 0
    def read(s, n):
        while s.b < n:
            byte = s.d[s.p]; s.p += 1
            s.v |= byte << s.b; s.b += 8
        r = s.v & ((1 << n) - 1); s.v >>= n; s.b -= n
        return r
    def align(s):
        s.v = 0; s.b = 0

def parse_entry(d, p):
    br = BR(d, p)
    off = br.read(31); same = br.read(1)
    if same:
        sz = br.read(32); us = cs = sz
    else:
        us = br.read(32); cs = br.read(32)
    comp = br.read(6); hb = br.read(1)
    blocks = 0
    if hb:
        blocks = br.read(32)
    enc = br.read(1)
    cbs = br.read(32)
    bl = []
    if blocks:
        for i in range(blocks):
            s = br.read(31); e = br.read(1)
            bl.append((s, e))
    return dict(off=off, us=us, cs=cs, comp=comp, blocks=blocks, enc=enc, cbs=cbs, bl=bl), br.p

# Parse ALL entries sequentially from the start of the encoded region.
# The encoded region starts after the header. From my earlier parse:
# mount(14) + numEntries(4) + seed(8) + hasPHI(4) + phOff(8) + phSize(8) + phHash(20) + hasFDI(4) + fdOff(8) + fdSize(8) + fdHash(20) + encCount(4)
# = 14+4+8+4+8+8+20+4+8+8+20+4 = 110
p = 110
entries = []
while p < len(idx) - 10:
    e, np = parse_entry(idx, p)
    if e["off"] > 340087368 or e["us"] > 400000000 or e["comp"] > 5:
        print(f"BAD at {p}: {e}")
        break
    entries.append(e)
    p = np
print(f"parsed {len(entries)} entries, ended at {p}")
for e in entries[:5]:
    print(e["off"], e["us"], e["cs"], e["comp"], e["blocks"])
