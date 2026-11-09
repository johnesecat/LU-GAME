import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
f.seek(339628863)
idx = f.read(165602)

# Let me try the ACTUAL UE5 format from source (FPakFile::DecodePakEntry in UnrealPak.cpp):
#   uint32 Offset = ReadBits(31)  -- NO wait.
# Real UE5.1 DecodePakEntry:
#   int64 Offset; uint32 Size, UncompressedSize; uint32 CompressionMethodIndex;
#   ReadValue(Offset, 31+1)? 
# From UE source (I'll reconstruct from memory of the actual code):
#   static void DecodeInternal(FBitReader& Reader, FPakEntry& Entry)
#   {
#       uint32 Value = Reader.ReadBits(31)? 
# Actually the real code is:
#   Entry.Offset = ReadBits(31); bool bSameSize = ReadBit();
#   if (!bSameSize) { Entry.UncompressedSize = ReadBits(32); Entry.Size = ReadBits(32); }
#   else { Entry.UncompressedSize = Entry.Size = ReadBits(32); }  <- maybe!
#   Entry.CompressionMethodIndex = ReadBits(6)? or ReadBits(32)?
# Let me try: same-size case reads ONE 32-bit value for both sizes.
class BR:
    def __init__(s, d, p):
        s.d = d; s.p = p; s.v = 0; s.b = 0
    def read(s, n):
        while s.b < n:
            byte = s.d[s.p]; s.p += 1
            s.v |= byte << s.b; s.b += 8
        r = s.v & ((1 << n) - 1); s.v >>= n; s.b -= n
        return r

# Try the last file (KawaiiPhysics.uplugin, enc=165476) — a small text file
for enc in (165476, 165464):
    br = BR(idx, enc)
    off = br.read(31); same = br.read(1)
    if same:
        sz = br.read(32)
        us = cs = sz
    else:
        us = br.read(32); cs = br.read(32)
    comp = br.read(6); hb = br.read(1)
    blocks = br.read(32) if hb else 0
    encb = br.read(1)
    cbs = br.read(32)
    print(f"enc={enc}: off={off} same={same} us={us} cs={cs} comp={comp} blocks={blocks} enc={encb} cbs={cbs}")
    # If sizes look wrong, try reading offset as 32 bits
    br2 = BR(idx, enc)
    off2 = br2.read(32)
    print(f"  alt: off32={off2}")
