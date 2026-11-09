import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
f.seek(339628863)
idx = f.read(165602)
# At 230: "00 00 00 E0 00 20 00 00 15 03 00 00 00 00 00 E0 4A 23 00 00"
# Pattern: "00 00 00 E0" then "00 20 00 00" then "15 03 00 00" then "00 00 00 E0" then "4A 23 00 00"
# 0x315 = 789, 0x234A = 9034. And "00 20 00 00" = 0x2000 = 8192.
# I see "E0" appearing every ~8 bytes. 0xE0 = 1110 0000.
# What if each entry is 8 bytes: [31-bit offset][1-bit flag][32-bit size]?
# Entry at 230: bytes "00 00 00 E0 00 20 00 00" -> offset bits 0-30 = 0, bit31 = 1 (from E0 bit7)
# Hmm E0 bit7 = 1. So offset=0, flag=1. Then size 32 bits from "00 20 00 00" = 8192?
# But wait — maybe the bit layout is: [offset 31][flag 1] packed in 4 bytes, then [size 32] in 4 bytes.
# "00 00 00 E0" as LE u32 = 0xE0000000. 31 bits = 0x60000000, bit31 = 1.
# offset = 0x60000000?? No...
# LSB-first bit reading of "00 00 00 E0": 
#   byte0=0x00: bits 0-7 = 0
#   byte1=0x00: bits 8-15 = 0
#   byte2=0x00: bits 16-23 = 0
#   byte3=0xE0: bits 24-31 = 0,0,0,0,0,1,1,1
# 31-bit offset = bits 0-30 = 0 (bits 24-28 are 0, bits 29,30 = 1!) 
# WAIT: bits 24-31 of byte3 E0 LSB-first: bit24=0(E0 bit0), bit25=0(bit1), bit26=0(bit2), bit27=0(bit3), bit28=0(bit4), bit29=1(bit5), bit30=1(bit6), bit31=1(bit7)
# So offset = bits 29,30 set = 0x60000000 = 1610612736. flag = bit31 = 1.
# That's what the tool printed: off=1610612736 same=1.
# 1610612736 = 0x60000000. Hmm... what if offsets are stored SHIFTED? 0x60000000 >> 5 = 0x3000000 = 50331648. No.
# What if the offset is 32 bits and I should read 32 bits: 0xE0000000 = 3758096384. >> 4 = 234881024. No.
# Hmm, what if these aren't offsets at all? What if the encoded region has a different structure?
# Let me look at the UE5.1 source more carefully. From UnrealPak.cpp (5.1):
#   void DecodePakEntry(const uint8* SourcePtr, FPakEntry& Decoder, ...)
#   {
#       FMemoryBitReader BitReader(SourcePtr, MaxSerialSize...);
#       uint32 Value = BitReader.ReadBits(31)? NO.
# Actually the real code:
#   static void DecodeInternal(FBitReader& Reader, FPakEntry& Entry)
#   {
#       uint32 Offset = Reader.ReadBits(31)?? 
# I recall the actual UE5 code is:
#   Entry.Offset = (int64)Reader.ReadBits(31) ... no wait, it's ReadSerializedUInt?
# Hmm. Let me look at it from the DATA side. I know:
#   - File 1 (BreakOutFloat2Components.uasset): offset 0, size 807, usize 807, comp 0
#   - File 2 (its .uexp): offset 860, size 243, usize 243, comp 0
# The encoded region should contain these values somewhere. Let me search for the bit pattern
# of "807" (0x327) and "243" (0xF3) near the start of the encoded region.
# 807 = 0b1100100111 (10 bits). 243 = 0b11110011 (8 bits).
# In the bytes at 110: "00 E0 00 00 00 00 27 03 00 00 00 00 00 E0 5C 03 00 00 F3 00..."
# "27 03" = 807 LE! And "F3 00" = 243 LE! And "5C 03" = 860 LE!
# So the values ARE stored as plain LE integers, but preceded by "00 E0" patterns!
# Sequence: [00 E0] [00 00 00 00] [27 03 00 00] [00 00 00 00] [00 E0] [5C 03 00 00] [F3 00 00 00]...
# Hmm: "00 E0 00 00 00 00" then "27 03 00 00" then "00 00 00 00 00 E0" then "5C 03 00 00" then "F3 00 00 00"
# What if each entry is: [flags byte(s)] [offset 8B] [size 4B] [usize 4B]?
# Entry 1: flags="00 E0 00 00 00 00"?? offset="27 03 00 00"=807?? No, offset should be 0.
# What if: [00 E0] = flags, [00 00 00 00] = offset(4B)=0, [27 03 00 00] = size=807, [00 00 00 00]... 
# Hmm but then usize? 
# Let me look at the pattern differently:
# "00 E0 | 00 00 00 00 | 00 00 27 03 | 00 00 00 00 | 00 E0 | 5C 03 00 00 | F3 00 00 00 | 00 E0 | 00 08 00 00 | 0F 03 00 00"
# If entries are 10 bytes: [2B flags][4B offset][4B size]:
# E1: flags=0xE000, offset=0x0300_0000?? no.
# Try: [00 E0 00 00] [00 00 27 03] [00 00 00 00] -> 12 bytes: flags=0xE0000000? offset=0x03270000? size=0?
# Try reading as: u32 at 110 = 0xE0000000, u32 at 114 = 0x03270000, u32 at 118 = 0x00000000
# Hmm 0x03270000 = 53084160. 
# What about: the bit stream packs [31-bit offset][1-bit flag][32-bit size] but the FIRST entry's
# offset is 0 and flag=1, so bits = 0x80000000 | 0 = "00 00 00 80". We see "00 E0 00 00" instead.
# 0xE0 = 1110 0000. If bits are MSB-first: 1,1,1,0,0,0,0,0 -> the first 3 bits are 1.
# What if the format starts with a 3-bit type tag? Like 111 = "full entry follows"?
# I'm going in circles. Let me try to find UE5.1's actual DecodePakEntry code online.
print("searching web for UE5 pak entry decode format")
