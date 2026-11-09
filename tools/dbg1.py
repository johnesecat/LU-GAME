import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
f.seek(1156)
d = f.read(120)
print(" ".join(f"{b:02X}" for b in d[:120]))
