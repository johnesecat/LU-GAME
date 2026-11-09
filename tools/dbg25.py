import struct, zlib
data = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb").read()
off = 156436480
h = data[off:off+80]
print("header bytes 0-79:")
for i in range(0, 80, 16):
    print(f"  [{i:3d}]", " ".join(f"{b:02X}" for b in h[i:i+16]))
# fields
o, s, u = struct.unpack_from("<qqq", h, 0)
comp, = struct.unpack_from("<i", h, 24)
print(f"offset={o} size={s} usize={u} comp={comp}")
# hash 20 bytes at 28..47
print("hash:", h[28:48].hex())
print("bytes 48-56:", " ".join(f"{b:02X}" for b in h[48:57]))
nb, = struct.unpack_from("<I", h, 48)
print("NumBlocks:", nb)
print("flags byte:", h[52])
cbs, = struct.unpack_from("<I", h, 53)
print("cbs:", cbs)
# block table at 57
print("block table first 64 bytes:")
bt = h[57:80]
print("  ", " ".join(f"{b:02X}" for b in bt))
# try u32 pairs
for i in range(2):
    a, b = struct.unpack_from("<II", h, 57 + i*8)
    print(f"  u32 pair[{i}]: {a} {b}")
# try u64 pairs from 57
for i in range(1):
    a, b = struct.unpack_from("<qq", h, 57 + i*16)
    print(f"  u64 pair[{i}]: {a} {b}")
