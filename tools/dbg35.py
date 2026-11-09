import struct
data = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb").read()
fsize = len(data)
magic_at = data.rfind(b"\xE1\x12\x6F\x5A", fsize - 4096)
footer = data[magic_at:]
# Footer = 204 bytes: magic(4) version(4) idxOff(8) idxSize(8) hash(20) = 44
# then "Zlib" + zeros from 44 to 203 = 160 bytes = 5 x 32-byte method slots.
# So NO encrypted-index flag in this footer (v11 layout: methods come last, no flag? or flag is 0).
# Actually in UE5.1: FPakInfo has Magic, Version, IndexOffset, IndexSize, IndexHash,
# bEncryptedIndex, CompressionMethods[5]. If bEncryptedIndex were at 44, "Zlib" would be at 45.
# But "Zlib" is at 44. So either there's no flag, or the flag is at the END (204 = OOB).
# Conclusion: index is NOT encrypted (we parsed it fine), and the only compression method is "Zlib".
# So comp slot 1 = Zlib. But zlib.decompress on the block data fails...
# UNLESS the "Zlib" blocks are actually raw DEFLATE without the 2-byte header!
# The data starts with "78 9C" which IS a zlib header. But decompressobj produced 0 bytes...
# Hmm wait — maybe I fed it the wrong slice. Let me re-examine where block data starts.
# For GlobalShaderCache: entry offset=156436480, header 57 bytes + block table 98*16 = 1568.
# 57 + 1568 = 1625. Data at off+1625. But WAIT — maybe the block table is only present
# in the INDEX, not inline! The inline header might be shorter!
# In UE5, the inline header at the entry offset contains the FULL FPakEntry serialization
# INCLUDING the block table. But maybe for this pak, the data starts right after a shorter header.
# Let me scan from off+57 for the zlib magic 78 9C:
h = data[off:off+3100000] if False else None
off = 156436480
# scan for 78 9C in the first 2000 bytes after off:
region = data[off:off+2000]
for i in range(len(region)-1):
    if region[i] == 0x78 and region[i+1] == 0x9C:
        print(f"78 9C at offset {off+i} (entry+{i})")
        if i > 1500: break
