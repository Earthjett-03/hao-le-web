import asyncio,json,re,sys,time,urllib.request,urllib.parse,concurrent.futures
from pathlib import Path
import edge_tts
ROOT=Path(__file__).parent
rows=json.loads((ROOT/'hsk-data.json').read_text(encoding='utf-8'))
corrections=json.loads((ROOT/'hsk-corrections.json').read_text(encoding='utf-8'))
cachepath=ROOT/'sources/thai-cache.json'
cache=json.loads(cachepath.read_text(encoding='utf-8')) if cachepath.exists() else {}

def translate_batch(batch):
    missing=[r for r in batch if str(r['id']) not in cache]
    if not missing:return
    q='\n'.join(f"{r['id']}. {r['word']}" for r in missing)
    url='https://translate.googleapis.com/translate_a/single?'+urllib.parse.urlencode(dict(client='gtx',sl='zh-CN',tl='th',dt='t',q=q))
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req,timeout=40) as response: result=json.load(response)
            text=''.join(x[0] for x in result[0] if x[0])
            values={m.group(1):m.group(2).strip() for m in re.finditer(r'(?m)^\s*(\d+)\s*[.．、)]\s*(.+)$',text)}
            if any(not values.get(str(r['id'])) for r in missing):
                if len(missing)>1:
                    mid=len(missing)//2
                    translate_batch(missing[:mid]);translate_batch(missing[mid:]);return
                if text.strip():values[str(missing[0]['id'])]=re.sub(r'^\s*\d+[.．、)]\s*','',text).strip()
                else:raise ValueError('Empty translation')
            cache.update({str(r['id']):values[str(r['id'])] for r in missing})
            cachepath.write_text(json.dumps(cache,ensure_ascii=False),encoding='utf-8')
            return
        except Exception:
            if attempt==3:raise
            time.sleep(2**attempt)

def translations():
    for i in range(0,len(rows),25):
        translate_batch(rows[i:i+25])
        if i%250==0:print('Thai translations',min(i+25,len(rows)),flush=True)
        time.sleep(.15)
    overrides=json.loads((ROOT/'thai-overrides.json').read_text(encoding='utf-8'))
    for r in rows:
        key=str(r['id'])
        r['thai']=overrides.get(key,cache[key])
        r['reviewed']=key in overrides
    (ROOT/'hsk-data.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print('Thai complete',len(rows),flush=True)

async def audio():
    out=ROOT/'hsk-audio';out.mkdir(exist_ok=True)
    semaphore=asyncio.Semaphore(4)
    done=0
    failures=[]
    async def generate(r):
        nonlocal done
        target=out/f"{r['id']}.mp3"
        async with semaphore:
            # A pinyin correction can change the intended pronunciation even
            # when the Chinese spelling is unchanged, so do not reuse its clip.
            refresh_audio='pinyin' in corrections.get(str(r['id']),{})
            if refresh_audio or not(target.exists() and target.stat().st_size>1000):
                for attempt in range(4):
                    try:
                        await asyncio.wait_for(edge_tts.Communicate(r['word'],'zh-CN-XiaoxiaoNeural',rate='-15%').save(str(target)),timeout=45)
                        if target.stat().st_size<1000:raise ValueError('Short audio')
                        break
                    except Exception:
                        if attempt==3:failures.append(r['id'])
                        else:await asyncio.sleep(2**attempt)
            done+=1
            if done%100==0:print('Audio',done,'/',len(rows),'failed',len(failures),flush=True)
    await asyncio.gather(*(generate(r) for r in rows))
    if failures:raise RuntimeError(f'Audio failed: {failures}')
    print('Audio complete',done,flush=True)

async def main():
    if '--audio-only' in sys.argv:
        await audio()
        return
    results=await asyncio.gather(asyncio.to_thread(translations),audio(),return_exceptions=True)
    for result in results:
        if isinstance(result,Exception):raise result
asyncio.run(main())
