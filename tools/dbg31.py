import struct, zlib
data = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb").read()
off = 156436480
h = data[off:off+1700]
d0 = h[1625:1625+31532]
# zlib header 78 9C is present but stream is "incomplete or truncated" — because block0's
# compressed size isn't 31532. The cumulative values might be UNCOMPRESSED ends!
# If 31532 is the uncompressed end of block0... but cbs=65536, so block0 should be 65536 uncompressed.
# Hmm. What if the values are compressed sizes per block (not cumulative)?
# block0 csize=31532? Then zlib.decompress(d0) should work if d0 is exactly block0.
# It failed with "incomplete or truncated" — meaning d0 has valid zlib start but ends early/late.
# Maybe block0 is smaller. Let me use zlib decompressobj and see how many bytes it consumes:
d = zlib.decompressobj()
try:
    out = d.decompress(d0)
    print("consumed:", len(d0) - len(d.unconsumed_tail), "produced:", len(out))
except Exception as e:
    print("err:", e)
# Try feeding byte by byte to find where block0 ends:
d = zlib.decompressobj()
out = b""
i = 0
try:
    while i < len(d0):
        chunk = d.decompress(d0[i:i+1])
        out += chunk
        i += 1
        if d.eof:
            break
    print(f"block0: consumed {i} bytes, produced {len(out)} uncompressed, eof={d.eof}")
except Exception as e:
    print("err at", i, e)
