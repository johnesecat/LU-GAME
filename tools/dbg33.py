import struct, zlib
data = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb").read()
off = 156436480
h = data[off:off+1700]
region = h[1625:1625+3089304]
d = zlib.decompressobj()
out = d.decompress(region)
print("produced:", len(out), "eof:", d.eof, "unused:", len(d.unconsumed_tail))
# produced 0 with no error — the decompressor is waiting for more data? That's odd for 3MB input.
# Unless the stream is a "stored" block... or the data isn't zlib at all despite 78 9C.
# WAIT. Maybe the data is Oodle! UE5's default is Oodle. The footer said "Zlib" but maybe
# the compression methods list has more entries I didn't parse. Let me re-check the footer.
fsize = len(data)
magic_at = data.rfind(b"\xE1\x12\x6F\x5A", fsize - 4096)
footer = data[magic_at:]
print("footer bytes:", " ".join(f"{b:02X}" for b in footer[:80]))
# UE5 footer: magic(4) version(4) indexOffset(8) indexSize(8) hash(20) encrypted(1) compMethods(5*32)
magic, version = struct.unpack_from("<II", footer, 0)
io, isz = struct.unpack_from("<qq", footer, 8)
print(f"magic={magic:X} v={version} idxOff={io} idxSize={isz}")
print("hash:", footer[24:44].hex())
print("encrypted flag:", footer[44])
print("comp methods bytes 45-60:", " ".join(f"{b:02X}" for b in footer[45:61]))
# comp methods are 32-byte FStrings? In v11: after hash(20) + encrypted(1), there's
# an array of compression method names (up to 5, each a 32-byte fixed buffer? or FStrings?)
# Let me look at the raw text:
print("footer as text 45-200:", footer[45:200])
