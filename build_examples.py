"""Compile authored examples; never invent a sentence for an uncovered word."""
import asyncio, hashlib, json, re, sys, unicodedata
from functools import lru_cache
from pathlib import Path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / '.audio-tools'))
from pypinyin import lazy_pinyin, pinyin, Style, load_phrases_dict
load_phrases_dict({word:[[syllable] for syllable in reading.split()] for word,reading in {
    '说得':'shuō de','跑得':'pǎo de','飞得':'fēi de','读得':'dú de','写得':'xiě de','做得':'zuò de',
    '来得':'lái de','照得':'zhào de','跳得':'tiào de','长得':'zhǎng de','起得':'qǐ de',
    '高兴地':'gāo xìng de','认真地':'rèn zhēn de','慢慢地':'màn màn de',
    '我们得':'wǒ men děi','你得':'nǐ děi','我得':'wǒ děi','得分':'dé fēn',
    '教我们':'jiāo wǒ men','教我':'jiāo wǒ','教你':'jiāo nǐ','教书':'jiāo shū',
    '难受':'nán shòu','相处':'xiāng chǔ','哪所':'nǎ suǒ','这所':'zhè suǒ'
}.items()})
load_phrases_dict({'好玩儿': [['hǎo'], ['wán'], ['r']], '面条儿': [['miàn'], ['tiáo'], ['r']], '一点儿': [['yì'], ['diǎn'], ['r']], '哪儿': [['nǎ'], ['r']], '那儿': [['nà'], ['r']], '这儿': [['zhè'], ['r']]})
rows = json.loads((ROOT / 'hsk-data.json').read_text(encoding='utf-8'))
def unaccent(text):
    return ''.join(c for c in unicodedata.normalize('NFD',text) if not unicodedata.combining(c))
def split_reading(word, reading):
    # Match syllables to characters instead of splitting joined pinyin heuristically.
    for variant in reading.split('/'):
        value=re.sub(r"[\s'’·-]",'',variant.lower())
        def visit(i,rest):
            if i==len(word):return [] if not rest else None
            candidates=set(pinyin(word[i],heteronym=True,style=Style.TONE)[0])
            candidates.update(unaccent(s) for s in list(candidates))
            if word[i]=='儿':candidates.add('r')
            if word[i] in '一不':candidates.update(['yī','yí','yì'] if word[i]=='一' else ['bù','bú'])
            for syllable in sorted(candidates,key=len,reverse=True):
                if rest.startswith(syllable):
                    tail=visit(i+1,rest[len(syllable):])
                    if tail is not None:return [syllable]+tail
            return None
        found=visit(0,value)
        if found is not None:return found
    return None
official_readings={r['id']:split_reading(r['word'],r['pinyin']) for r in rows}
load_phrases_dict({r['word']:[[s] for s in official_readings[r['id']]] for r in rows if len(r['word'])>1 and official_readings[r['id']]})
neutral_words=[r for r in sorted(rows,key=lambda r:len(r['word']),reverse=True) if len(r['word'])>1 and official_readings[r['id']] and any(unaccent(s)==s for s in official_readings[r['id']])]
@lru_cache(None)
def compounds(word):
    return [r['word'] for r in rows if len(r['word'])>len(word) and word in r['word']]
@lru_cache(None)
def target_start(zh,word):
    starts=[m.start() for m in re.finditer(re.escape(word),zh)]
    for start in starts:
        if not any(m.start()<=start and m.end()>=start+len(word) for compound in compounds(word) for m in re.finditer(re.escape(compound),zh)):
            return start
    return starts[0] if starts else -1
def make_example(zh,thai,target_ids=()):
    tokens=lazy_pinyin(zh,style=Style.TONE,errors=lambda s:list(s))
    assert len(tokens)==len(zh)
    # Longer dictionary phrases can mask neutral tones in shorter familiar words.
    for r in neutral_words:
        reading=official_readings[r['id']]
        if len(r['word'])>1 and reading and any(unaccent(s)==s for s in reading):
            for match in re.finditer(re.escape(r['word']),zh):tokens[match.start():match.end()]=reading
    # Use the official reading at a target's standalone occurrence, avoiding e.g. 教室 for 教.
    for target_id in target_ids:
        row=rows[target_id-1];word=row['word'];reading=official_readings[target_id]
        if not reading:continue
        start=target_start(zh,word)
        if start>=0 and not any(m.start()<=start and m.end()>=start+len(word) for compound in compounds(word) for m in re.finditer(re.escape(compound),zh)):
            tokens[start:start+len(word)]=reading
    pin=re.sub(r'\s+([，。！？、])',r'\1',' '.join(tokens))
    return {'zh':zh,'pinyin':pin,'thai':thai,'audio':hashlib.sha256(zh.encode()).hexdigest()[:16]}
sentences = []
for line in (ROOT / 'examples-source.txt').read_text(encoding='utf-8').splitlines():
    if not line.strip(): continue
    zh, thai = line.split('|')
    assert zh and re.search(r'[\u0e00-\u0e7f]', thai)
    pin = ' '.join(lazy_pinyin(zh, style=Style.TONE, neutral_tone_with_five=False))
    pin = re.sub(r'\s+([，。！？、])', r'\1', pin)
    sentences.append({'zh': zh, 'pinyin': pin, 'thai': thai, 'audio': hashlib.sha256(zh.encode()).hexdigest()[:16]})
# Explicit choices prevent short words being illustrated only inside another word.
preferred = {'边':'学校旁边', '病':'他的病', '不':'我不喝', '饭':'这家饭店', '国':'我想去外国', '好':'对，你', '后':'上课后', '开':'请开', '课':'我们上午', '口':'你家有几口', '男':'那个男学生', '女':'那个女学生', '年':'我们在这里住', '前':'吃饭前', '人':'今天来的人', '上':'桌子上', '事':'我有一件事', '书':'这是我的第一', '睡':'弟弟已经睡', '说':'对，你', '天':'我在北京住', '听':'我喜欢听', '下':'书在椅子下', '学':'我想学做', '些':'我想买些', '雨':'今天的雨', '字':'这个字', '做':'昨天我在家做', '多':'今天来的人很多', '家':'我家在学校旁边', '玩':'孩子们在公园里玩', '要':'我明天要去医院'}
result = {}
for r in rows:
    if r['level'] != 1: continue
    candidates = [s for s in sentences if r['word'] in s['zh']]
    if r['word'] in preferred:
        candidates = [s for s in candidates if s['zh'].startswith(preferred[r['word']])]
    if candidates:
        chosen=candidates[0]
        if r['word']=='少':chosen=next(s for s in sentences if s['zh'].startswith('今天来的人'))
        result[str(r['id'])] = make_example(chosen['zh'],chosen['thai'],[r['id']])
for source in sorted(ROOT.glob('examples-level*.txt')):
    for line in source.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        ids, zh, thai = line.split('|')
        example = make_example(zh,thai,[int(k) for k in ids.split(',')])
        for key in ids.split(','):
            assert key not in result, ('Duplicate target',key)
            assert rows[int(key)-1]['word'] in zh, (key,rows[int(key)-1]['word'],zh)
            assert re.search(r'[\u0e00-\u0e7f]',thai)
            result[key]={**example,'start':target_start(zh,rows[int(key)-1]['word'])}
for key,example in result.items():
    example.setdefault('start',target_start(example['zh'],rows[int(key)-1]['word']))
missing = [(r['id'], r['word']) for r in rows if str(r['id']) not in result]
print('Coverage:',len(result),'/ 3600; missing:',len(missing),flush=True)
if '--require-all' in sys.argv: assert not missing, missing
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
