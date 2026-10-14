"""Read-only audit of the extracted game archive; counts pointer-backed FMG entries."""
import collections
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parent
MAGIC = b'\0\0\1\0'
JP = re.compile('[ぁ-ヺ一-龯々〆ヵヶｦ-ﾟ]')

def clean(s):
    s = re.sub(r'<[^>]*>', '', s)
    s = re.sub(r'##[a-zA-Z]\[[^\]]*\]', '', s)
    return s.strip()

def fmg(x, start=0):
    if x[start:start+4] != MAGIC or start+28 > len(x):
        return None
    size, zero, groups, count, table, reserved = struct.unpack_from('<6I', x, start+4)
    if zero or reserved or not 0 < groups <= count < 20000:
        return None
    if table != 28+12*groups or table+count*4 > size or start+size > len(x):
        return None
    ids = []
    for g in range(groups):
        base, first, last = struct.unpack_from('<3I', x, start+28+12*g)
        if base != len(ids) or first > last or last-first+1 > count:
            return None
        ids.extend(range(first,last+1))
    if len(ids) != count or ids != sorted(set(ids)):
        return None
    entries = []
    for i, ident in enumerate(ids):
        p = struct.unpack_from('<I', x, start+table+4*i)[0]
        if not p:
            continue
        if not table+count*4 <= p < size:
            return None
        end = x.find(b'\0',start+p,start+size)
        if end < 0:
            return None
        try:
            s = x[start+p:end].decode('cp932')
        except UnicodeDecodeError:
            return None
        if any(ord(c)<32 and c not in '\r\n\t' for c in s):
            return None
        entries.append(dict(id=ident,offset=p,text=s,clean_text=clean(s),japanese=bool(JP.search(clean(s)))))
    return dict(offset=start,size=size,slots=count,entries=entries,
                sha256=hashlib.sha256(x[start:start+size]).hexdigest())

def scan(x):
    tables=[]
    end=0
    for m in re.finditer(re.escape(MAGIC),x):
        if m.start()<end:
            continue
        t=fmg(x,m.start())
        if t:
            tables.append(t)
            end=m.start()+t['size']
    return tables

def decompress_csc(x):
    assert x[:4] == b'\0\1\0\0' and x[8:12] == b'\0'*4
    size = struct.unpack_from('>I',x,4)[0]
    assert 0 < size < 100_000_000
    out = bytearray()
    p = 12
    while len(out) < size:
        flags = x[p]
        p += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags >> bit & 1:
                a, b = x[p:p+2]
                p += 2
                source = max(0,len(out)-4096) + (a << 4) + (b >> 4)
                length = (b & 15) + 1
                assert source < len(out)
                if source + length <= len(out):
                    out.extend(out[source:source+length])
                else:
                    for k in range(length):
                        out.append(out[source+k])
            else:
                out.append(x[p])
                p += 1
    assert len(out) == size
    assert len(x)-p <= 32, (len(x),p,len(x)-p)
    return bytes(out)

def named_bnd_children(x):
    if x[:8] != b'BND\0\xff\xff\0\0':
        return []
    n = struct.unpack_from('<I',x,16)[0]
    children = []
    for i in range(n):
        ident, offset, size, np = struct.unpack_from('<4I',x,32+i*16)
        assert offset+size <= len(x)
        name = x[np:x.index(0,np)].decode('cp932') if np else str(ident)
        children.append(dict(id=ident,offset=offset,size=size,path=name))
    return children

def main():
    data=(ROOT/'source/DATA.BIN').read_bytes()
    inventory=json.loads((ROOT/'inventory.json').read_text(encoding='utf8'))
    tables=[]
    compressed_audit=[]
    for r in inventory:
        x=data[r['offset']:r['offset']+r['size']]
        compressed = r['path'].lower().endswith('.csc')
        if compressed:
            x=decompress_csc(x)
            compressed_audit.append(dict(source=r['path'],compressed_bytes=r['size'],decompressed_bytes=len(x)))
        children=named_bnd_children(x)
        for t in scan(x):
            inner=next((c['path'] for c in children if c['offset']<=t['offset']<c['offset']+c['size']),None)
            t.update(source=r['path'],inner_source=inner,compressed=compressed,archive_index=r['index'],archive_offset=None if compressed else r['offset']+t['offset'])
            tables.append(t)
    (ROOT/'fmg_tables.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2),encoding='utf8')
    (ROOT/'compressed_audit.json').write_text(json.dumps(compressed_audit,indent=2),encoding='utf8')
    print('Decompressed and checked:',len(compressed_audit),'files')
    grouped=collections.defaultdict(list)
    for t in tables:
        grouped[t['source']].append(t)
    print('Validated tables:',len(tables),'across files:',len(grouped))
    for path,ts in grouped.items():
        entries=[e for t in ts for e in t['entries']]
        print(path,'tables',len(ts),'nonempty',sum(bool(e['text']) for e in entries),'Japanese',sum(e['japanese'] for e in entries))
    entries=[e for t in tables for e in t['entries']]
    print('TOTAL nonempty',sum(bool(e['text']) for e in entries),'JP',sum(e['japanese'] for e in entries))
    print('UNIQUE raw',len({e['text'] for e in entries if e['text']}),'JP',len({e['clean_text'] for e in entries if e['japanese']}))

if __name__=='__main__':
    main()
