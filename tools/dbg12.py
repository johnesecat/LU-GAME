import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
f.seek(339628863)
idx = f.read(165602)
# off=595189760 = 0x237C0000. Hmm. 595189760 / 16 = 37199360. Interesting: 595189760 = 0x237C_0000.
# What if the offset is stored SHIFTED LEFT by some bits? 595189760 >> 4 = 37199360 — plausible pak offset!
# Or the bit reader is misaligned by a few bits. Let me look at the raw bytes at enc=165476:
print("bytes at 165476:", " ".join(f"{b:02X}" for b in idx[165476:165476+20]))
# And at enc=165464:
print("bytes at 165464:", " ".join(f"{b:02X}" for b in idx[165464:165464+20]))
# And the first entry enc=120:
print("bytes at 120:", " ".join(f"{b:02X}" for b in idx[120:140]))
# The index ends at 165602. enc=165476 is near the end (126 bytes left).
# For a small .uplugin file (~200 bytes), the entry should be: offset ~339000000, size ~200.
# 339000000 = 0x143B64E00. Let's see if the bytes contain something like that.
