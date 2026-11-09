import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
# hdr@1099: off=9, size=0, usize=0, comp=garbage. Not a valid header at 1099.
# The hash "6E DB 1D 2C FC C9 6B 40 A1 41 41 1D 2A 12 82 7C 0B 00 00 00" appears at 1125-1144.
# If hash ends at 1144, then blocks at 1145-1148, enc 1149, and data at 1150? But C1 is at 1152.
# If hash is at 1127-1146, blocks 1147-1150, enc 1151, data 1152 ✓. Then header starts at 1127-28 = 1099.
# comp at 1123-1126 = "00 00 00 00" ✓ (from row 1122: "00 00 6E DB..." -> 1122=00, 1123=00, 1124=00, 1125=6E)
# Hmm so hash starts at 1125, not 1127! Then: comp 1121-1124, usize 1113-1120, size 1105-1112, offset 1097-1104.
# Header at 1097: offset = bytes 1097-1104 = "00 00 00 00 00 00 00 00" = 0 ✓
# size = 1105-1112 = "00 00 00 00 00 00 00 00" = 0?? But the uasset is 896 bytes!
# ARGH. size=0 again. Unless... the uasset at 1152 is 896 bytes of which the header says size 0?
# Wait — maybe I have the wrong idea. What if these zero-size entries are REAL, and the "uasset" at 1152
# is actually just zeros + magic that happens to be part of a LARGER file's data?
# The uexp at 913 (size 243 per header at 860) spans 913..1156. The C1 83 2A 9E at 1152 is INSIDE
# the uexp data (913..1156)! It's the uexp's trailing magic! UE uexp files END with the package tag!
# YES! That's it! uexp files end with: [serial data][C1 83 2A 9E][serial size info]
# So the uexp at 913..1156 contains C1 83 2A 9E at 1152 as its TRAILER. 
# Then the next header at 1156 (all zeros, size 0) is a real zero-size entry (deleted file?),
# and the chain of zero-size entries 1156..2053 are all deleted/empty files.
# Then at 2053: header with size 783 (0x30F) -> data at 2106? But scan found C1 83 2A 9E F9 FF FF FF at 2101!
# 2053+53 = 2106 ≠ 2101. Hmm. 2101-53 = 2048. Header at 2048?
# From the earlier dump at 2046: bytes 2048-2055 = "00 00 0F 03 00 00 00 00"?? 
# Let me dump 2040..2110 with absolute offsets.
f.seek(2040)
d = f.read(75)
for i in range(0, 75, 8):
    end = min(i + 8, 75)
    print(2040 + i, " ".join(f"{b:02X}" for b in d[i:end]))
