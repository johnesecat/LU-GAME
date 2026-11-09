import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
f.seek(339628863)
idx = f.read(165602)
# off=1610612736 = 0x60000000. The bytes at 110: "00 00 00 E0 00 00 00 00 27 03 00 00..."
# Reading 31 bits LSB-first from "00 00 00 E0": bits 0-23 = 0, bits 24-30 from E0=1110 0000:
# E0 LSB-first: bit24=0, bit25=0, bit26=0, bit27=0, bit28=0, bit29=1, bit30=1, bit31=1
# 31-bit offset = bits 0..30 = 0 except bit29, bit30 = 1 -> offset = 0x60000000 = 1610612736. 
# Then bit31 = 1 -> same=1. Then size 32 bits from "00 00 00 00" = 0? But we got us=0, cs=0.
# Hmm wait, with same=1 we read one 32-bit = 0. Then comp 6 bits from "27" = 0x27=0010 0111 LSB-first: 1,1,1,0,0,1,0,0
# comp = 6 bits = 1,1,1,0,0,1 = 0b100111 = 39. Garbage.
# The offset 0x60000000 is wrong. But look: "27 03 00 00" = 807 — the size of the FIRST file!
# And "00 00 00 E0" before it... 
# WAIT A SECOND. What if the encoded entries DON'T start at 110? What if encCount at 106 is something else?
# Let me re-examine: maybe the layout is:
#   mount(14) numEntries(4) seed(8) hasPHI(4) phOff(8) phSize(8) phHash(20) hasFDI(4) fdOff(8) fdSize(8) fdHash(20) encCount(4) = 110
# and encCount=165488?? That's way more than 5619 files! 165488 must be the SIZE of the encoded entries region, not a count!
# Actually in UE5: "FilesNum" then the encoded entries follow. The value at 106 was 165488.
# Hmm, but 165602 - 110 = 165492. And 165488 ≈ 165492 - 4. So the "encCount" field IS the size!
# Wait no. Let me recheck what's at 106: from the byte dump earlier, bytes 106-109.
print("bytes 100-120:", " ".join(f"{b:02X}" for b in idx[100:120]))
# From the earlier dump: [106]=0x00? Let me print.
