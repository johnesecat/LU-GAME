import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
f.seek(339628863)
idx = f.read(165602)
# start=165478: off=339616633 (0x143E2379) — VALID PAK OFFSET! (just before the index at 339628863)
# So entries start 2 bytes after the FDI's enc value! I.e., enc + 2.
# But us=680, cs=3758096384 (garbage), comp=22 (garbage). The bit alignment must be different.
# off=339616633 is 31 bits. Then bit 31 = same flag. Then 32-bit usize, 32-bit csize...
# Let me read more carefully: after 31 bits + 1 bit = 32 bits = 4 bytes exactly.
# Bytes at 165478: "79 23 3E 14" = offset bits (31) + same bit (1) = exactly 32 bits!
# 0x143E2379 = 339616633. The 32nd bit (MSB of 0x14) = 0 -> same=0.
# Then usize = next 32 bits from "A8 02 00 00" = 0x2A8 = 680 ✓ (a .uplugin is ~680 bytes!)
# Then csize = next 32 bits from "00 00 00 00"?? = 0. But csize should be 680 too (uncompressed).
# Hmm wait: "A8 02 00 00 00 00 00 00" — if usize = 0x2A8 = 680 and csize = 0x000 = 0??
# Unless csize comes first! Let me try: csize=680, usize=0? No...
# OR: the "same" flag means sizes are equal, and only ONE 32-bit value follows.
# bit31 of "79 23 3E 14": 0x14 = 0001 0100. MSB (bit 31 of the 32-bit LE value) = 0. So same=0.
# Hmm. But maybe the flag is at a different position. Let me read: 31 bits offset, then 1 bit flag,
# then if flag=0: two 32-bit sizes. We got usize=680 (from A8 02 00 00) and csize=0 (from 00 00 00 00)?
# That means csize=0 — invalid. UNLESS the order is [csize][usize] and csize=680, usize=0? Also invalid.
# What if after the offset there's: [32-bit size][32-bit usize] where size=680 and usize=680?
# "A8 02 00 00" = 680, then next 4 bytes "00 00 00 00" = 0. Not 680.
# Wait, the bytes at 165478 are: "79 23 3E 14 A8 02 00 00 00 00 00 00 00 E0 56 26 3E 14 51 00"
# Hmm: "79 23 3E 14" (offset+flag), "A8 02 00 00" (680), "00 00 00 00" (0), "00 E0 56 26" ...
# What if it's: offset(31)+flag(1) = 32 bits, then size(32)=680, then... the NEXT entry starts?
# If csize==usize (uncompressed), maybe only ONE size is stored and the flag indicates this!
# The flag bit (bit 31 of first 32 bits) = 0... but maybe I have the flag inverted: 0 = same size!
# Then: offset=339616633, same_size=true, size=680. Then comp(6 bits), hasBlocks(1)...
# After reading 32+32 = 64 bits (8 bytes: "79 23 3E 14 A8 02 00 00"), next bits from "00 00 00 00 00 E0 56 26":
# byte8=0x00, byte9=0x00, byte10=0x00, byte11=0x00, byte12=0x00, byte13=0xE0...
# comp = 6 bits from byte8 = 0 ✓ (None)
# hasBlocks = 1 bit from byte8 bit6 = 0 ✓
# encrypted = 1 bit from byte8 bit7 = 0 ✓
# blockSize = 32 bits from remaining... = 0 ✓
# PERFECT! So the format is:
#   [31-bit offset][1-bit bSameSize]  (if bSameSize=0... wait no)
# Hmm, but the flag bit was 0 and we treated it as "same size". Let me re-examine:
# bit31 of "79 23 3E 14" (LE 32-bit = 0x143E2379): bit31 = (0x143E2379 >> 31) & 1 = 0 (since 0x14 < 0x80).
# So flag=0. And we read ONE size (680). So flag=0 means "sizes are the same, one value stored"?
# OR flag=0 means "not same" and we should read two values — but the second was 0.
# Let me check with a COMPRESSED file. Actually, let me check the first entry (enc=120, start=122):
class BR:
    def __init__(s, d, p):
        s.d = d; s.p = p; s.v = 0; s.b = 0
    def read(s, n):
        while s.b < n:
            byte = s.d[s.p]; s.p += 1
            s.v |= byte << s.b; s.b += 8
        r = s.v & ((1 << n) - 1); s.v >>= n; s.b -= n
        return r

def parse(start):
    br = BR(idx, start)
    off = br.read(31); same = br.read(1)
    if same:
        sz = br.read(32); us = cs = sz
    else:
        us = br.read(32); cs = br.read(32)
    comp = br.read(6); hb = br.read(1)
    blocks = br.read(32) if hb else 0
    enc = br.read(1)
    cbs = br.read(32)
    return dict(off=off, same=same, us=us, cs=cs, comp=comp, blocks=blocks, enc=enc, cbs=cbs)

# Test with flag=1 meaning "same": parse entry at 165478+... wait enc=165476, start=165478
# With my new understanding: flag bit = 0 means same? Let me just try both interpretations
for enc in (165476, 165464, 165452, 120, 132):
    br = BR(idx, enc + 2)
    off = br.read(31); flag = br.read(1)
    # interpretation A: flag=1 -> same size (one value)
    # interpretation B: flag=0 -> same size
    # Try A:
    brA = BR(idx, enc + 2)
    offA = brA.read(31); fA = brA.read(1)
    if fA:
        sz = brA.read(32); usA = csA = sz
    else:
        usA = brA.read(32); csA = brA.read(32)
    compA = brA.read(6); hbA = brA.read(1)
    print(f"enc={enc} (A): off={offA} flag={fA} us={usA} cs={csA} comp={compA} hb={hbA}")
