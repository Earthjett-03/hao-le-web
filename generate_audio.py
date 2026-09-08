import asyncio
from pathlib import Path
import edge_tts

WORDS = ['你好','谢谢','再见','对不起','没关系','我','你','名字','泰国人','很高兴','一','二','三','四','五','水','茶','米饭','面条','好吃','妈','麻','马','骂','吗','我喜欢茶']
TONES = {'妈','麻','马','骂','吗'}
OUT = Path(__file__).parent / 'audio'
OUT.mkdir(exist_ok=True)

async def main():
    limit = asyncio.Semaphore(3)
    async def make(word, mode):
        name = '-'.join(format(ord(c), 'x') for c in word)
        target = OUT / f'{name}-{mode}.mp3'
        rate = ('-35%' if mode == 'slow' else '-25%') if word in TONES else ('-25%' if mode == 'slow' else '-10%')
        async with limit:
            await edge_tts.Communicate(word, 'zh-CN-XiaoxiaoNeural', rate=rate).save(str(target))
            if target.stat().st_size < 1000:
                raise RuntimeError(f'Invalid audio: {target}')
    await asyncio.gather(*(make(w,m) for w in WORDS for m in ['normal','slow']))
    print('Generated 52 audio clips')

asyncio.run(main())
