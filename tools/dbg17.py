import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
f.seek(339628863)
idx = f.read(165602)
# bytes 100-109: "2E 88 06 83 9A B9 70 86 02 00" — the fdHash ends at 105 (20 bytes from 86..105).
# Wait: fdHash = bytes 86-105. Then bytes 106-109 = "00 00 00 00"?? 
# From dump: [100]=2E [101]=88 [102]=06 [103]=83 [104]=9A [105]=B9 [106]=70 [107]=86 [108]=02 [109]=00
# Hmm so fdHash might end at 105, and 106-109 = "70 86 02 00" = 165488 = encCount!
# Then encoded entries start at 110: "00 E0 00 00 00 00 27 03..."
# The first bits: "00 E0" — reading LSB-first: byte0=0x00, byte1=0xE0.
# What if the first entry's offset is 0 (the first file IS at offset 0)? 
# bits 0-30 = 0 (from 0x00 + low 7 bits of E0 = 0) -> offset = 0 ✓!!
# bit31 = high bit of E0 = 1 -> same=1?? 
# Hmm, but then size = 32 bits from "00 00 00 00" = 0. But the first file is 807 bytes!
# UNLESS same=1 means "read one size" and the size comes from "27 03 00 00" = 807!
# Let me recount: after 31+1 = 32 bits (bytes 0-3: "00 E0 00 00"), the next 32 bits = bytes 4-7 = "00 00 27 03"?? 
# Wait the bytes at 110: "00 E0 00 00 00 00 27 03 00 00 00 00 00 E0 5C 03..."
# byte0=0x00, byte1=0xE0, byte2=0x00, byte3=0x00, byte4=0x00, byte5=0x00, byte6=0x27, byte7=0x03
# 31-bit offset from bytes 0-3 (LSB-first): bits 0-7=0 (byte0), bits 8-15: E0 -> bits 8-12=0, bits 13,14,15=1
# bits 16-23 = 0 (byte2), bits 24-30 = 0 (byte3 low 7 bits)
# offset = (1<<13)|(1<<14)|(1<<15) = 0xE000 = 57344?? Not 0!
# Hmm. bit13,14,15 of E0: E0 = 1110 0000. LSB-first: bit0=0,bit1=0,bit2=0,bit3=0,bit4=0,bit5=1,bit6=1,bit7=1
# So bits 8-15 = 0,0,0,0,0,1,1,1 -> bit13=1, bit14=1, bit15=1
# offset = 0x2000+0x4000+0x8000 = 0xE000 = 57344. Not 0. 
# BUT WAIT — what if the offset is stored in the HIGH bits and I should read MSB-first?
# MSB-first from "00 E0 00 00": byte0=0x00 -> 8 zero bits, byte1=0xE0 -> MSB first: 1,1,1,0,0,0,0,0
# 31 bits MSB-first: 00000000 1110000 0... = 0b0000000011100000000000000000000 = 0xE00000?? 
# Hmm 31 bits: first 8 bits (byte0)=0, next 8 bits (byte1 MSB first)=1,1,1,0,0,0,0,0, next 8 (byte2)=0, next 7 (byte3)=0
# value = 0b00000000_11100000_00000000_0000000 = 0x00E00000 = 14680064. Not 0 either.
# OK here's another thought: what if the first entry is NOT at 110? What if there's a 4-byte "encoded data size" 
# at 106-109 (=165488) and entries start at 110, but the first entry has offset 0 and the "00 E0" is:
# Actually 0xE0 = 1110 0000. What if entries are written with a LEADING flag byte?
# Let me try: what if the format starts with [32-bit offset] where offset=0 for the first file?
# bytes 0-3 = "00 E0 00 00" = 0x0000E000 = 57344. Not 0.
# What if [31-bit offset][1-bit flag] where the first file's offset is 0 and flag=1:
# The value would be 0x80000000 = "00 00 00 80". We have "00 E0 00 00". 
# 0xE000 = 0b1110_0000_0000_0000. Hmm.
# What if there are TWO flag bits? [30-bit offset][2-bit flags]?
# Let me try a completely different tack: find the entry for a file whose offset I KNOW.
# The first file in FDI order is 'Lerp_Multiple_Float.uasset' with enc=120.
# From the pak walk, the file at offset 0 is 807 bytes (a uasset). Is that Lerp_Multiple_Float?
# The uasset at 53 contains "None" and other strings. Let me extract it and check.
f.seek(53)
data = f.read(807)
# find readable strings
import re
strings = re.findall(rb"[\x20-\x7e]{6,}", data)
for s in strings[:20]:
    print(s.decode("ascii", "replace"))
