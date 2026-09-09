import json, re, urllib.request, urllib.parse, time
from pathlib import Path
from collections import Counter
from pypdf import PdfReader

ROOT=Path(__file__).parent
cache=ROOT/'sources/vocabulary.txt'
if not cache.exists():
    reader=PdfReader(ROOT/'sources/hsk-2026.pdf')
    cache.write_text('\n'.join(p.extract_text() for p in reader.pages[79:169]),encoding='utf-8')
rows=[]
for block in [cache.read_text(encoding='utf-8')]:
    for line in block.splitlines():
        m=re.match(r'^(\d+)\s+([1-5])(?:（[^）]+）)*\s+(\S+)\s+(.+)$',line)
        if not m:
            if re.match(r'^\d+\s+[1-5]',line): print('UNPARSED',line,flush=True)
            continue
        idx,level,word,rest=m.groups()
        parts=re.split(r'\s+(?=[\u4e00-\u9fff（])',rest,maxsplit=1)
        rows.append(dict(id=int(idx),level=int(level),word=re.sub(r'[0-9]+$','',word),label=word,pinyin=parts[0].strip(),pos=parts[1] if len(parts)>1 else ''))
assert [r['id'] for r in rows]==list(range(1,3601)), f'Incomplete IDs: {len(rows)}'
out=ROOT/'hsk-data.json'
out.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print('Extracted',dict(Counter(r['level'] for r in rows)),flush=True)
