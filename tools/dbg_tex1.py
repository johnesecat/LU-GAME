import os, re, struct

# Verify: map_lips.ubulk = 5586944 = 2048^2 + 1024^2 + 512^2 + 256^2 + 128^2 (DXT5: 1 byte/pixel)
# So the texture is 2048x2048 with 5 mips. My heuristic must have picked wrong dims.
# Find the REAL structure: dump bytes around the PF_ string in the uexp.

def dump(name):
    uexp = os.path.join("extracted", name.replace("/", os.sep))
    d = open(uexp, "rb").read()
    m = re.search(rb"PF_[A-Z0-9]+\x00", d)
    if not m:
        print(name, ": no PF_"); return
    pf = m.group()[:-1].decode()
    at = m.end()
    print(f"=== {name.split('/')[-1]} fmt={pf} uexp={len(d)}B ===")
    print("  64 bytes after PF_ string:")
    seg = d[at:at+64]
    for i in range(0, 64, 16):
        print(f"    +{i:3d}", " ".join(f"{b:02X}" for b in seg[i:i+16]))
    # look for i32 pairs that could be dims
    print("  i32 values after PF_:")
    vals = []
    for i in range(0, 48, 4):
        v, = struct.unpack_from("<i", d, at+i)
        vals.append((i, v))
    print("   ", vals)
    # also 16 bytes BEFORE pf string
    print("  32 bytes before PF_ string:")
    seg2 = d[at-40:at]
    for i in range(0, 32, 16):
        print(f"    -{32-i:3d}", " ".join(f"{b:02X}" for b in seg2[i:i+16]))

dump("HDT/Content/characters/hdchan/materials/skin//map_lips.uexp")
dump("HDT/Content/characters/hdchan/materials/skin//lips_normal.uexp")
dump("HDT/Content/characters/hdchan/materials/skin//nipplemap.uexp")
