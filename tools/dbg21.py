import struct
data = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb").read()
idx = data[339628863:339628863+165602]
# flags=0 at enc=120 means: cbs=0, blocks=0, comp=0, all sizes u64.
# Then: offset u64 at 124 = "00 00 00 E0 5C 03 00 00"?? wait bytes 124-131.
# bytes at 120: [120]=00 [121]=00 [122]=00 [123]=00 [124]=00 [125]=E0 [126]=5C [127]=03 [128]=00 [129]=00 [130]=F3 [131]=00
# offset u64 at 124 = bytes 124-131 = "00 E0 5C 03 00 00 F3 00" = 0x00F300_00035CE000?? garbage.
# Hmm. But wait — maybe the FDI enc values are NOT byte offsets into idx! Maybe they're relative to
# the start of the encoded region (which begins after the encCount field at 110).
# enc=120 -> absolute 110+120 = 230. Let me check bytes at 230.
print("bytes at 230:", " ".join(f"{b:02X}" for b in idx[230:250]))
flags, = struct.unpack_from("<I", idx, 230)
print(f"flags@230 = 0x{flags:08X} = {flags:032b}")
# Also try: maybe enc is relative to index start + 4 (after mount)? Or the FDI enc is a byte offset
# but the encoded region starts at 110, so enc values ARE absolute (120 > 110 ✓).
# The issue: flags=0 at 120 gives garbage. What if the first 4 bytes at 120 aren't flags?
# What if entries are BIT-packed after all (not byte-aligned)?
# From the repak source: Entry::read_encoded reads a u32 flags word — that IS byte-aligned per entry?
# No! In repak, the encoded entries are read via a BitReader? Let me check the actual repak code.
# From the wiki: "A bit-encoded entry (pak v10+) starts with a u32" — so each entry starts with
# a u32 flags word. But entries might not be byte-aligned relative to each other!
# Actually in repak's read_encoded, the entries are read sequentially from a byte stream where
# each entry's fields follow the flags word. The FDI's enc value is a BYTE offset into the
# encoded data region. So enc=120 should be a valid entry start.
# flags=0 means: cbs=0 (no explicit block size), blocks=0, comp=0 (none), all u64 sizes.
# offset u64 = bytes 124-131. Let me decode: "00 E0 5C 03 00 00 F3 00" hmm wait I need to recount.
# idx[120:140] = "00 00 00 00 00 E0 5C 03 00 00 F3 00 00 00 00 00 00 E0 00 08"
# idx[120]=00 idx[121]=00 idx[122]=00 idx[123]=00 -> flags = 0x00000000
# idx[124]=00 idx[125]=E0 idx[126]=5C idx[127]=03 idx[128]=00 idx[129]=00 idx[130]=F3 idx[131]=00
# offset u64 = struct at 124 = 00 E0 5C 03 00 00 F3 00 -> LE = 0x00F30000035CE000 = huge. Garbage.
# So enc=120 is NOT the entry start for Lerp_Multiple_Float.uasset.
# MAYBE: the FDI enc values are relative to the encoded region start (110), so absolute = 110+enc.
# enc=120 -> 230. Let me decode at 230.
if True:
    pos = 230
    flags, = struct.unpack_from("<I", idx, pos); pos += 4
    print(f"flags = 0x{flags:08X}")
    cbs = (flags & 0x3F) << 11
    if (flags & 0x3F) == 0x3F:
        cbs, = struct.unpack_from("<I", idx, pos); pos += 4
    blocks = (flags >> 6) & 0xFFFF
    encrypted = (flags >> 22) & 1
    comp = (flags >> 23) & 0x3F
    size32 = (flags >> 29) & 1
    usize32 = (flags >> 30) & 1
    off32 = (flags >> 31) & 1
    print(f"cbs={cbs} blocks={blocks} enc={encrypted} comp={comp} size32={size32} usize32={usize32} off32={off32}")
    if off32:
        offset, = struct.unpack_from("<I", idx, pos); pos += 4
    else:
        offset, = struct.unpack_from("<Q", idx, pos); pos += 8
    print(f"offset={offset}")
    if usize32:
        usize, = struct.unpack_from("<I", idx, pos); pos += 4
    else:
        usize, = struct.unpack_from("<Q", idx, pos); pos += 8
    print(f"usize={usize}")
