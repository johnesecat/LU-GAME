import struct, zlib
data = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb").read()
off = 156436480
h = data[off:off+1700]
# decompressobj consumed 75 bytes and produced 0 — that's just buffering. The stream needs
# more input. So block0 is bigger than 75 bytes obviously. The issue is finding block boundaries.
# Let me try: decompress the ENTIRE compressed region as one zlib stream:
region = h[1625:1625+3089304]
d = zlib.decompressobj()
try:
    out = d.decompress(region)
    print("whole region zlib:", len(out), "eof:", d.eof)
except Exception as e:
    print("whole region fail:", e)
# If that fails, try raw deflate on whole region:
d2 = zlib.decompressobj(-15)
try:
    out2 = d2.decompress(region)
    print("whole region raw deflate:", len(out2), "eof:", d2.eof)
except Exception as e:
    print("raw deflate fail:", e)
