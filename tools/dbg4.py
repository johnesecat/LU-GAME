import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
# OK so C1 83 2A 9E is at 1152 only. My manual counting of the dump was off (the dump had 75 bytes but
# I misread positions). Let me print with absolute offsets.
f.seek(1090)
d = f.read(75)
for i in range(0, 75, 8):
    end = min(i + 8, 75)
    print(1090 + i, " ".join(f"{b:02X}" for b in d[i:end]))
