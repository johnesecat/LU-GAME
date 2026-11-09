import struct
data = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb").read()
idx = data[339628863:339628863+165602]
# 2431 bad entries. The first entry (enc=120) decoded to garbage offset 68398419397107712.
# Let me look at the raw bytes at enc=120 and manually decode.
print("bytes at 120:", " ".join(f"{b:02X}" for b in idx[120:140]))
# flags u32 at 120:
flags, = struct.unpack_from("<I", idx, 120)
print(f"flags = 0x{flags:08X} = {flags:032b}")
print(f"  bits0-5 (cbs>>11): {flags & 0x3F}")
print(f"  bits6-21 (blocks): {(flags >> 6) & 0xFFFF}")
print(f"  bit22 (enc): {(flags >> 22) & 1}")
print(f"  bits23-28 (comp): {(flags >> 23) & 0x3F}")
print(f"  bit29 (size32): {(flags >> 29) & 1}")
print(f"  bit30 (usize32): {(flags >> 30) & 1}")
print(f"  bit31 (off32): {(flags >> 31) & 1}")
