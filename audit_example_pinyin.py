"""Report target readings for manual contextual review; not a correctness score."""
import runpy, unicodedata, re
from pathlib import Path
scope=runpy.run_path(str(Path(__file__).with_name('build_examples.py')))
compact=lambda s: ''.join(c for c in s.lower() if c.isalpha())
for row in scope['rows']:
    ex=scope['result'].get(str(row['id']))
    if not ex:continue
    zh=ex['zh'];word=row['word'];start=ex.get('start',zh.find(word))
    tokens=re.findall(r'[^\W\d_]+|[^\w\s]',ex['pinyin'])
    assert len(tokens)==len(zh),(zh,tokens)
    actual=' '.join(tokens[start:start+len(word)])
    if compact(actual)!=compact(row['pinyin']):
        print(f"{row['id']}|{word}|{row['pinyin']}|{actual}|{zh}")
