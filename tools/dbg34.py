import struct
data = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb").read()
fsize = len(data)
magic_at = data.rfind(b"\xE1\x12\x6F\x5A", fsize - 4096)
footer = data[magic_at:]
# footer: magic(4) version(4) idxOff(8) idxSize(8) hash(20) = 44 bytes
# byte 44 = 0x90?? "encrypted flag: 90" — hmm 0x90 = 1001 0000.
# Then "5A 6C 69 62" = "Zlib"! So the compression method name starts at byte 44!
# Layout: ... hash(20) ends at 44. Then compression method names as 32-byte null-padded strings.
# byte 44 = 0x5A = 'Z', 45='l', 46='i', 47='b' -> "Zlib" then nulls.
# So there's NO encrypted flag byte before the comp methods? Or the encrypted flag is elsewhere.
# In UE5 v11 footer: magic(4) version(4) indexOffset(8) indexSize(8) indexHash(20)
#   then bEncryptedIndex(1) then compressionMethods (array of 5 x 32-byte names)
# But here byte 44 = 0x5A = 'Z' — so the encrypted flag must be BEFORE the hash or absent.
# Actually wait: "FA B8 61 FE 80 43 01 A5 7F 1B EF 1E FB 8D E2 B7 C7 9E 89 76" is 20 bytes = hash at 24-43.
# Then byte 44 = 0x5A = 'Z'. Hmm, but where's the encrypted flag?
# In v11: after the hash comes: uint8 bEncryptedIndex, then TArray<FString> CompressionMethods
# stored as: int32 count, then count * FString(32 bytes fixed? no, FString = i32 len + chars)
# Hmm, but "Zlib" appears directly at 44. Let me check if maybe the layout is:
#   hash(20)@24, then compMethods as 5 fixed 32-byte buffers starting at 44.
# 44 + 5*32 = 204. Footer total = 44 + 20 + 160 = 224? The footer is 221 bytes (magic_at to EOF).
# fsize - magic_at = ?
print("footer length:", fsize - magic_at)
# 221 bytes. 44 (magic+ver+off+size) + 20 (hash) = 64. 221 - 64 = 157.
# If compMethods = 5 * 32 = 160, that's 224 total > 221. Close but no.
# What if: hash(20)@24, encrypted(1)@44, then 4 methods * 32 = 128? 44+1+128 = 173. no.
# Let me look at bytes 44-52: "5A 6C 69 62 00 00 00 00" = "Zlib\0\0\0\0"
# and the rest is all zeros until the end. So it's ONE method name "Zlib" in a fixed buffer.
# 221 - 44 = 177 bytes for methods. 177 / 32 = 5.5. Hmm.
# Actually maybe: encrypted flag is at 44? 0x5A = 90 = 'Z'. If encrypted flag were 0 or 1, 
# then 'Z' can't be it. So no encrypted flag, OR it's packed elsewhere.
# In UE 5.1 v11: FPakInfo::Serialize: Magic, Version, IndexOffset, IndexSize, IndexHash(20),
#   bEncryptedIndex(uint8), CompressionMethods (5 x 32 bytes), then if version>=10:
#   ... actually the order might be: Magic(4) Version(4) IndexOffset(8) IndexSize(8)
#   IndexHash(20) CompressionMethods(5*32=160) bEncryptedIndex(1) = 4+4+8+8+20+160+1 = 205
# 221 - 205 = 16. Hmm, what are the last 16 bytes?
print("last 40 bytes:", " ".join(f"{b:02X}" for b in footer[-40:]))
# From the earlier dump the last bytes were mostly zeros. Let me check if there's a "Zlib" 
# at 44 followed by 4 more 32-byte slots (all empty), then encrypted flag at 44+160=204.
# footer[204] = ?
print("footer[204]:", footer[204] if len(footer) > 204 else "OOB")
print("footer[200:221]:", " ".join(f"{b:02X}" for b in footer[200:221]))
