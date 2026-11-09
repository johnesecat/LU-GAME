#!/usr/bin/env python3
"""Universal UE5 mesh extractor: f32/f16 positions, u32/u16 indices -> compact .bin."""
import os, struct, json

def f16(v):
    s = (v >> 15) & 1; e = (v >> 10) & 0x1F; m = v & 0x3FF
    if e == 0: return (m * 2**-24) * (-1 if s else 1)
    if e == 31: return float('nan')
    return ((1 + m/1024) * 2**(e-15)) * (-1 if s else 1)

def extract(path):
    d = open(path,'rb').read()
    n = len(d)
    best16 = (0, None)
    i = 0
    while i < n - 6:
        a, b, c = struct.unpack_from('<HHH', d, i)
        x, y, z = f16(a), f16(b), f16(c)
        if all(-500 < v < 500 and v == v for v in (x,y,z)):
            s = i; c2 = 0
            while i < n - 6:
                a, b, c = struct.unpack_from('<HHH', d, i)
                x, y, z = f16(a), f16(b), f16(c)
                if all(-500 < v < 500 and v == v for v in (x,y,z)):
                    c2 += 1; i += 6
                else: break
            if c2 > best16[0]: best16 = (c2, s)
        else: i += 2
    best32 = (0, None)
    i = 0
    while i < n - 12:
        x, y, z = struct.unpack_from('<fff', d, i)
        if all(-500 < v < 500 and v == v for v in (x,y,z)):
            s = i; c2 = 0
            while i < n - 12:
                x, y, z = struct.unpack_from('<fff', d, i)
                if all(-500 < v < 500 and v == v for v in (x,y,z)):
                    c2 += 1; i += 12
                else: break
            if c2 > best32[0]: best32 = (c2, s)
        else: i += 4
    cands = []
    if best16[0] >= 100: cands.append(('f16', best16[1], best16[0]))
    if best32[0] >= 100: cands.append(('f32', best32[1], best32[0]))
    if not cands: return None
    cands.sort(key=lambda t: -t[2])
    fmt, pstart, vcount = cands[0]
    i = pstart - 4; s = pstart
    while i >= 0:
        v, = struct.unpack_from('<I', d, i)
        if v < vcount: s = i; i -= 4
        else: break
    ic32 = (pstart - s)//4
    if ic32 < 100:
        i = pstart - 2; s2 = pstart
        while i >= 0:
            v, = struct.unpack_from('<H', d, i)
            if v < vcount: s2 = i; i -= 2
            else: break
        ic16 = (pstart - s2)//2
        if ic16 >= 100:
            return fmt, pstart, vcount, s2, ic16, 2
        return fmt, pstart, vcount, None, 0, 0
    return fmt, pstart, vcount, s, ic32, 4

fl = open('extracted/_filelist.txt').read().splitlines()
os.makedirs('web/assets/meshes', exist_ok=True)
manifest = {}
done = 0
for n in fl:
    if not n.endswith('.uexp'): continue
    p = os.path.join('extracted', n.replace('/', os.sep))
    if os.path.getsize(p) < 5000: continue
    head = open(p,'rb').read(4096)
    if b'PF_' in head: continue
    try: r = extract(p)
    except Exception: continue
    if not r: continue
    fmt, pstart, vcount, istart, icount, iwidth = r
    d = open(p,'rb').read()
    rel = n[len('HDT/Content/'):].replace('//','/')
    out = os.path.join('web/assets/meshes', rel[:-5] + '.bin').replace('/', os.sep)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    blob = bytearray()
    blob += struct.pack('<IIB', vcount, icount, 0 if fmt=='f32' else 1)
    if fmt == 'f32':
        blob += d[pstart:pstart+vcount*12]
    else:
        for i in range(vcount):
            a, b, c = struct.unpack_from('<HHH', d, pstart + i*6)
            blob += struct.pack('<fff', f16(a), f16(b), f16(c))
    if icount > 0 and istart is not None:
        if iwidth == 4:
            blob += d[istart:istart+icount*4]
        else:
            for i in range(icount):
                v, = struct.unpack_from('<H', d, istart + i*2)
                blob += struct.pack('<I', v)
    else:
        for i in range(vcount):
            blob += struct.pack('<I', i)
    open(out,'wb').write(bytes(blob))
    manifest[rel] = dict(v=vcount, i=icount, fmt=fmt)
    done += 1
print('exported', done, 'meshes')
json.dump(manifest, open('web/assets/meshes/manifest.json','w'), indent=1)
top = sorted(manifest.items(), key=lambda kv: -kv[1]['v'])[:15]
for k, v in top:
    print('  %7d verts  %s' % (v['v'], k))
