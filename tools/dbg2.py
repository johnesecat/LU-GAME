import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
# The region 1156..2053 is all zeros (897 bytes). The uasset at 1152 has header at 1099.
# So: uexp data 913..1099 (186 bytes), then header 1099..1152 (53 bytes), uasset 1152..?
# Next uasset at 2101 -> header at 2048. So uasset at 1152 has size 2048-1152 = 896 bytes.
# And the zero region 1156..2048 is INSIDE the uasset data (1152..2048)! 
# A uasset that's mostly zeros? That's a uasset with version 0 (UE5.1+ uses version 0 = "unversioned").
# Wait, the uasset at 1152 starts with C1 83 2A 9E 00 00 00 00 (version 0). Then 8 zeros, then... all zeros?
# Hmm, that means the uasset content is: tag(4) version(4) then zeros. That's a "null" uasset?
# Actually NO. Let me re-read the dump from 1100: after C1 83 2A 9E at 1152, bytes 1156+ = 00 00 00 00 00 00 00 00
# then "0B 03 00 00 00 00 00 00" at 1164? From the earlier dump at 1100 (120 bytes):
# 1100: 00... (24 zeros) 1124: 6E DB 1D 2C FC C9 6B 40 A1 41 41 1D 2A 12 82 7C (16B hash)
# 1140: 0B 00 00 00 00 00 00 00 00 00 00 C1 83 2A 9E 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 0
# So the uasset at 1152 = C1 83 2A 9E 00 00 00 00 + 888 zeros = 896 bytes total.
# That's a uasset with only a header and no content — an EMPTY package! These are common for
# redirector/dummy assets. OK so my walk WAS correct, except the header at 1099 (not 1156).
# The walk went: 860 (hdr 53B) -> data 913 size 243 -> next 1156. But actual next header is 1099!
# 1099 = 913 + 186. So the uexp size is 186, not 243. The header at 860 said 243.
# 243 - 186 = 57. AH: maybe the header at 860 is 57 bytes (860+57=917)? No, data at 913.
# OR: the uexp at 913 is 243 bytes BUT the next header at 1099 overlaps it? Impossible.
# Let me look at bytes 1090..1160 to see the transition.
f.seek(1090)
d = f.read(75)
print(" ".join(f"{b:02X}" for b in d))
