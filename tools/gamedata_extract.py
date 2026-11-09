#!/usr/bin/env python3
"""Extract all game data tables + dialogue + stringtables from the UE5 pak into JSON
for the Bevy web port.

DataTable row format (cooked UE5.1): each row = FName(i32 len + chars + NUL) rowname,
then the row struct: FName(i32 len + chars + NUL) property-name, then type tag + value.
We parse the common patterns: FName properties, FloatProperty, BoolProperty, IntProperty,
and FLinearColor (4 floats).
"""
import struct, re, os, json

SRC = "extracted"
OUT = "web/assets/data"
os.makedirs(OUT, exist_ok=True)

def rd_fstr(d, p):
    n, = struct.unpack_from("<i", d, p)
    if n <= 0 or p + 4 + n > len(d):
        return None, p
    s = d[p+4:p+4+n-1].decode("utf-8", "replace")
    return s, p + 4 + n

def parse_row_data(d, p, end):
    """Parse tagged properties until 'None' FName or end."""
    out = {}
    while p < end - 8:
        name, p2 = rd_fstr(d, p)
        if name is None:
            break
        if name == "None":
            p = p2
            break
        # type tag follows
        tag, p3 = rd_fstr(d, p2)
        if tag is None:
            break
        if tag == "FloatProperty":
            v, = struct.unpack_from("<f", d, p3)
            out[name] = v
            p = p3 + 4
        elif tag == "BoolProperty":
            out[name] = bool(d[p3])
            p = p3 + 1
        elif tag == "IntProperty":
            v, = struct.unpack_from("<i", d, p3)
            out[name] = v
            p = p3 + 4
        elif tag == "NameProperty" or tag == "StrProperty":
            v, p4 = rd_fstr(d, p3)
            out[name] = v
            p = p4
        elif tag == "StructProperty":
            # struct header: FName struct-name, FName type-name, i64 size, then data
            sname, q = rd_fstr(d, p3)
            tname, q2 = rd_fstr(d, q)
            size, = struct.unpack_from("<q", d, q2)
            q3 = q2 + 8
            if tname == "LinearColor":
                r, g, b, a = struct.unpack_from("<ffff", d, q3)
                out[name] = [r, g, b, a]
                p = q3 + 16
            else:
                # skip
                p = q3 + size
        else:
            # unknown tag: bail (row parse desync)
            break
    return out, p

def parse_datatable(path):
    d = open(path, "rb").read()
    rows = []
    pos = 0
    while pos < len(d) - 40:
        n, = struct.unpack_from("<i", d, pos)
        if 30 <= n <= 40 and pos + 4 + n <= len(d):
            s = d[pos+4:pos+4+n-1]
            try:
                name = s.decode("ascii")
            except Exception:
                pos += 1
                continue
            if re.match(r"^[0-9A-F]{32}$", name):
                data_start = pos + 4 + n
                # find next row start to bound this row's data
                nxt = len(d)
                q = data_start
                while q < len(d) - 40:
                    m, = struct.unpack_from("<i", d, q)
                    if 30 <= m <= 40 and q + 4 + m <= len(d):
                        t = d[q+4:q+4+m-1]
                        try:
                            tn = t.decode("ascii")
                            if re.match(r"^[0-9A-F]{32}$", tn):
                                nxt = q
                                break
                        except Exception:
                            pass
                    q += 1
                props, _ = parse_row_data(d, data_start, nxt)
                rows.append({"id": name, "props": props})
                pos = data_start
                continue
        pos += 1
    return rows

def parse_stringtable(path):
    """StringTable: rows of (key, source, translation)."""
    d = open(path, "rb").read()
    out = {}
    pos = 0
    while pos < len(d) - 8:
        k, p = rd_fstr(d, pos)
        if k is None or not k:
            pos += 1
            continue
        s, p2 = rd_fstr(d, p)
        if s is None:
            pos += 1
            continue
        t, p3 = rd_fstr(d, p2)
        if t is None:
            pos += 1
            continue
        # accept only if all three look like text and lengths are sane
        if 0 < len(k) < 200 and len(s) < 2000 and len(t) < 2000:
            out[k] = t if t else s
            pos = p3
        else:
            pos += 1
    return out

def parse_dialogue(path):
    """Dialogue table: rows keyed by event name with a list of lines."""
    d = open(path, "rb").read()
    txt = d.decode("utf-8", "replace")
    return txt

tables = {
    "positions": "HDT/Content/gameplay/positions/dt_positions.uexp",
    "session_scalars": "HDT/Content/gameplay/session/dt_session_scalars.uexp",
    "session_booleans": "HDT/Content/gameplay/session/dt_session_booleans.uexp",
    "session_integers": "HDT/Content/gameplay/session/dt_session_integers.uexp",
    "session_combos": "HDT/Content/gameplay/session/dt_session_combos.uexp",
    "session_ranges": "HDT/Content/gameplay/session/dt_session_ranges.uexp",
    "session_radials": "HDT/Content/gameplay/session/dt_session_radials.uexp",
    "session_hsvs": "HDT/Content/gameplay/session/dt_session_hsvs.uexp",
    "session_names": "HDT/Content/gameplay/session/dt_session_names.uexp",
    "env_colors": "HDT/Content/environment/dt_envcolors.uexp",
    "arm_styles": "HDT/Content/characters/dude/arms/styles/dt_armstyles.uexp",
    "penis_styles": "HDT/Content/characters/dude/dick/materials/dt_penisstyles.uexp",
}
result = {}
for key, rel in tables.items():
    p = os.path.join(SRC, rel.replace("/", os.sep))
    if not os.path.exists(p):
        print("missing:", rel)
        continue
    rows = parse_datatable(p)
    result[key] = rows
    print(f"{key}: {len(rows)} rows")

# stringtables
sts = {
    "combos": "HDT/Content/gameplay/session/stringtable_session-combos.uexp",
    "game_ui": "HDT/Content/UI/sringtable_game-ui.uexp",
    "common": "HDT/Content/UI/stringtable_common.uexp",
}
for key, rel in sts.items():
    p = os.path.join(SRC, rel.replace("/", os.sep))
    if not os.path.exists(p):
        print("missing:", rel)
        continue
    result["st_" + key] = parse_stringtable(p)
    print(f"st_{key}: {len(result['st_'+key])} keys")

# dialogue (plain text format from HDT/Content/Dialogue/default.txt + the cooked table)
dlg_path = os.path.join(SRC, "HDT/Content/gameplay/dialogue/default/dt_dialogue_default.uexp")
if os.path.exists(dlg_path):
    result["dialogue_default_raw"] = parse_dialogue(dlg_path)
    print("dialogue_default: raw", len(result["dialogue_default_raw"]), "chars")
# also the plain-text dialogue file
txt_path = r"HDT\Content\Dialogue\default.txt"
if os.path.exists(txt_path):
    result["dialogue_txt"] = open(txt_path, encoding="utf-8", errors="replace").read()
    print("dialogue_txt:", len(result["dialogue_txt"]), "chars")

with open(os.path.join(OUT, "gamedata.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, indent=1, ensure_ascii=False)
print("wrote gamedata.json")

# summary
for k, v in result.items():
    if isinstance(v, list):
        print(f"  {k}: {len(v)} rows")
        for r in v[:3]:
            print(f"    {r['id'][:12]}... {json.dumps(r['props'])[:120]}")
    elif isinstance(v, dict):
        print(f"  {k}: {len(v)} keys")
