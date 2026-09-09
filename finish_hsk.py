import json
from pathlib import Path
ROOT=Path(__file__).parent
rows=json.loads((ROOT/'hsk-data.json').read_text(encoding='utf-8'))
thai=json.loads((ROOT/'thai-overrides.json').read_text(encoding='utf-8'))
for path in sorted(ROOT.glob('thai-manual-*.json')):
    values=json.loads(path.read_text(encoding='utf-8'))
    assert not (thai.keys() & values.keys()), f'Duplicate translations in {path}'
    thai.update(values)
assert set(thai)=={str(n) for n in range(1,3601)}
for row in rows:
    row['thai']=thai[str(row['id'])]
    row['reviewed']=True
    row.pop('english',None)
    row.pop('dictionarySource',None)
    assert row['thai'].strip() and row['word'] and row['pinyin']
    audio=ROOT/'hsk-audio'/f"{row['id']}.mp3"
    assert audio.exists() and audio.stat().st_size>1000,f'Missing audio {audio}'
(ROOT/'hsk-data.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('Assembled 3600 vocabulary entries, Thai meanings and audio references')
