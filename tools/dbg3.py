import struct
f = open(r"HDT\Content\Paks\HDT-WindowsNoEditor.pak", "rb")
# From 1090: "00 10 00 00 00 00 00 00 | 00 09 00 00 00 00 00 00 | 00 00 00 00 | 6E DB 1D 2C FC C9 6B 40 A1 41 41 1D 2A 12 82 7C 0B 00 00 00 | 00 00 00 00 | 00 | C1 83 2A 9E"
# Positions: 1090-1097 (8B), 1098-1105 (8B), 1106-1109 (4B), 1110-1129 (20B hash), 1130-1133 (4B), 1134 (1B), 1135: C1 83 2A 9E
# Hmm wait: 1090+45 = 1135. But earlier I found C1 at 1152! Let me count the dump: 75 bytes from 1090.
# idx0=00 idx1=10 idx2=00 idx3=00 idx4=00 idx5=00 idx6=00 idx7=00 (1090-1097)
# idx8=00 idx9=09 idx10=00 idx11=00 idx12=00 idx13=00 idx14=00 idx15=00 (1098-1105)
# idx16-19 = 00 00 00 00 (1106-1109)
# idx20-39 = 6E DB 1D 2C FC C9 6B 40 A1 41 41 1D 2A 12 82 7C 0B 00 00 00 (1110-1129)
# idx40-43 = 00 00 00 00 (1130-1133)
# idx44 = 00 (1134)
# idx45 = C1 (1135)?? But scan said C1 at 1152!
# The dump shows C1 83 2A 9E at dump index 45,46,47,48 -> file offset 1135,1136,1137,1138.
# But my scan found the pattern at 1152. Both can't be right unless there are TWO occurrences.
# Let me search for all C1 83 2A 9E in 1090..1160.
f.seek(1090)
d = f.read(80)
pat = bytes.fromhex("C1832A9E")
i = 0
while True:
    i = d.find(pat, i)
    if i < 0:
        break
    print("found at", 1090 + i)
    i += 1
