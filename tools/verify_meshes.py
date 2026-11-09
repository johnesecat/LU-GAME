import struct, os, json
m = json.load(open('web/assets/meshes/manifest.json'))
for name in ['characters/hdchan/models/sm_hdchan.uexp',
             'characters/dude/dick/materials/standard/sm_dude_dick.uexp',
             'characters/dude/dick/materials/popsicle/dude_popsicle.uexp',
             'characters/hdchan/clothing/items/dresses/maid/sm_maid-dress.uexp']:
    p = os.path.join('web/assets/meshes', name.replace('.uexp', '.bin'))
    d = open(p, 'rb').read()
    vc, ic, fmt = struct.unpack_from('<IIB', d, 0)
    xs = []; ys = []; zs = []
    for i in range(0, min(vc, 2000)):
        x, y, z = struct.unpack_from('<fff', d, 9 + i * 12)
        xs.append(x); ys.append(y); zs.append(z)
    base = os.path.basename(name)
    print('%s: v=%d i=%d fmt=%d size=%d' % (base, vc, ic, fmt, len(d)))
    print('  x:[%.1f,%.1f] y:[%.1f,%.1f] z:[%.1f,%.1f]' % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    exp = 9 + vc * 12 + ic * 4
    print('  size ok: %s (%d vs %d)' % (len(d) == exp, len(d), exp))
