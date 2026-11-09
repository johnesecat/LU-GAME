import struct
data = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb").read()
idx = data[339628863:339628863+165602]
# At 230: flags=0xE0000000 -> off32=1, usize32=1, size32=1, comp=0, blocks=0
# offset u32 at 234 = "00 20 00 00" = 8192, usize u32 at 238 = "15 03 00 00" = 789.
# Hmm offset=8192? But the first file should be at 0... unless this isn't the first file.
# Wait — FDI order: first file is Lerp_Multiple_Float.uasset. Maybe it IS at offset 8192?
# But we found a uasset at offset 0 (data at 53) which is BreakOutFloat2Components.
# Hmm, but wait: offset 8192 with the inline header... the pak entry offset points to the START
# of the inline FPakEntry header! So data at 8192+53 = 8245? Let me check: is there a uasset at 8245?
# From the earlier scan: uasset hits included 8245! YES!
# So: entry offset 8192 -> inline header at 8192 (53 bytes) -> data at 8245.
# And the file at offset 0 (data at 53) is a DIFFERENT file (BreakOutFloat2Components).
# So the base for FDI enc values is 110 (start of encoded region). enc=120 -> absolute 230. ✓
# Let me now verify: Lerp_Multiple_Float.uasset at offset 8192, size 789.
f = data
print("header at 8192:", " ".join(f"{b:02X}" for b in f[8192:8192+53]))
print("data at 8245 starts:", " ".join(f"{b:02X}" for b in f[8245:8245+16]))
# Also check: what file is at offset 0? Its entry would have enc such that 110+enc points to it.
# Let me find which enc value decodes to offset 0. Search the encoded region for flags with offset=0.
# Actually, let me just re-run the full extraction with base 110.
