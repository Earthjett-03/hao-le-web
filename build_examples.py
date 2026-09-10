"""Compile authored examples; never invent a sentence for an uncovered word."""
import asyncio, hashlib, json, re, sys
from pathlib import Path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / '.audio-tools'))
from pypinyin import lazy_pinyin, Style, load_phrases_dict
load_phrases_dict({'好玩儿': [['hǎo'], ['wán'], ['r']], '面条儿': [['miàn'], ['tiáo'], ['r']], '一点儿': [['yì'], ['diǎn'], ['r']], '哪儿': [['nǎ'], ['r']], '那儿': [['nà'], ['r']], '这儿': [['zhè'], ['r']]})
rows = json.loads((ROOT / 'hsk-data.json').read_text(encoding='utf-8'))
sentences = []
for line in (ROOT / 'examples-source.txt').read_text(encoding='utf-8').splitlines():
    if not line.strip(): continue
    zh, thai = line.split('|')
    assert zh and re.search(r'[\u0e00-\u0e7f]', thai)
    pin = ' '.join(lazy_pinyin(zh, style=Style.TONE, neutral_tone_with_five=False))
    pin = re.sub(r'\s+([，。！？、])', r'\1', pin)
    sentences.append({'zh': zh, 'pinyin': pin, 'thai': thai, 'audio': hashlib.sha256(zh.encode()).hexdigest()[:16]})
# Explicit choices prevent short words being illustrated only inside another word.
preferred = {'边':'学校旁边', '病':'他的病', '不':'我不喝', '饭':'这家饭店', '国':'我想去外国', '好':'对，你', '后':'上课后', '开':'请开', '课':'我们上午', '口':'你家有几口', '男':'那个男学生', '女':'那个女学生', '年':'我们在这里住', '前':'吃饭前', '人':'今天来的人', '上':'桌子上', '事':'我有一件事', '书':'这是我的第一', '睡':'弟弟已经睡', '说':'对，你', '天':'我在北京住', '听':'我喜欢听', '下':'书在椅子下', '学':'我想学做', '些':'我想买些', '雨':'今天的雨', '字':'这个字', '做':'昨天我在家做'}
result = {}
for r in rows:
    if r['level'] != 1: continue
    candidates = [s for s in sentences if r['word'] in s['zh']]
    if r['word'] in preferred:
        candidates = [s for s in candidates if s['zh'].startswith(preferred[r['word']])]
    if candidates: result[str(r['id'])] = candidates[0]
missing = [(r['id'], r['word']) for r in rows if r['level']==1 and str(r['id']) not in result]
print('Coverage:',len(result),'/ 300; missing:',missing,flush=True)
(ROOT/'hsk-examples.json').write_text(json.dumps(result, ensure_ascii=False, separators=(',',':')),encoding='utf-8')
async def audio():
    import edge_tts
    folder=ROOT/'example-audio';folder.mkdir(exist_ok=True)
    unique={s['audio']:s for s in result.values()}
    limit=asyncio.Semaphore(3)
    async def make(key,s):
        target=folder/(key+'.mp3')
        async with limit:
            if target.exists() and target.stat().st_size>1000:return
            for attempt in range(3):
                try:
                    await asyncio.wait_for(edge_tts.Communicate(s['zh'],'zh-CN-XiaoxiaoNeural',rate='-15%').save(str(target)),45)
                    assert target.stat().st_size>1000
                    return
                except Exception:
                    if attempt==2:raise
                    await asyncio.sleep(2**attempt)
    await asyncio.gather(*(make(k,s) for k,s in unique.items()))
    print('Audio complete:',len(unique),flush=True)
if '--audio' in sys.argv:asyncio.run(audio())
