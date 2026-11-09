import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
# hdr@1096: off=150994944 (0x09000000) — the "09" is at position 3 of the header. So offset field
# would be "00 00 00 09 00 00 00 00" = 0x09000000. Not 0. Invalid.
# Let me try to think about it differently. The 16 bytes 6E DB 1D 2C FC C9 6B 40 A1 41 41 1D 2A 12 82 7C
# look like a GUID (random). In UE pak entries there's no GUID... but in .uasset files there IS a GUID!
# uasset structure: [tag 4][version 4][...][GUID 16]...
# The uasset at 1152: C1 83 2A 9E 00 00 00 00 then... all zeros? A uasset normally has:
#   Tag(4), LegacyFileVersion(4), LegacyUE3Version(4), FileVersionUE4(4), ..., GUID(16), ...
# If the uasset at 1152 is "C1 83 2A 9E 00 00 00 00" + zeros, it's an empty/minimal uasset.
# BUT the 16 GUID-like bytes at 1124-1139 come BEFORE the uasset start (1152). 
# What if there's ANOTHER uasset ending right before? Like the uexp at 913 is followed by
# another file whose header is at ... hmm.
# Let me look at the bigger picture: dump 900..1160 fully.
f.seek(900)
d = f.read(260)
for i in range(0, 260, 16):
    end = min(i + 16, 260)
    print(900 + i, " ".join(f"{b:02X}" for b in d[i:end]))
