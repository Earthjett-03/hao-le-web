const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const rows=JSON.parse(fs.readFileSync('hsk-data.json','utf8'));
const examples=JSON.parse(fs.readFileSync('hsk-examples.json','utf8'));
assert.equal(Object.keys(examples).length,3600);
for(const r of rows){
  const e=examples[r.id];assert(e&&e.zh&&e.pinyin&&/[\u0e00-\u0e7f]/.test(e.thai),'Missing example '+r.id);
  assert.equal(e.zh.slice(e.start,e.start+r.word.length),r.word,'Incorrect highlight '+r.id);
  assert.match(e.audio,/^[a-f0-9]{16}$/);
  const b=fs.readFileSync('example-audio/'+e.audio+'.mp3');assert(b.length>1000);
  assert(b.subarray(0,3).toString()==='ID3'||(b[0]===255&&(b[1]&224)===224));
}
for(const [id,zh,thai,pinyin] of [
  [357,'买这块手表花了我五百元。','ใช้จ่ายเงินหรือเวลา'],
  [358,'红色的花旁边有绿色的叶子。','ดอกไม้'],
  [403,'请看纸的另一面。','ด้าน / หน้า / พื้นผิว'],
  [486,'到下一站后，我们骑自行车回家。','สถานี / ป้าย'],
  [966,'请站起来，活动一下。','ยืน'],
  [1650,'云南省是我最喜欢的省份之一，省会是昆明。','มณฑล'],
  [2767,'我们在饭馆点了两碗面。','แป้ง / เส้นบะหมี่'],
  [2998,'骑车上班可以省钱。','ประหยัด / ลด'],
  [3184,'这种做法不为大家所接受。','ถูก… (รูปถูกกระทำ)','wèi']
]){
  assert.equal(examples[id].zh,zh,'Incorrect corrected example '+id);
  assert.equal(rows[id-1].thai,thai,'Incorrect corrected meaning '+id);
  if(pinyin) assert.equal(rows[id-1].pinyin,pinyin,'Incorrect corrected pinyin '+id);
}
for(const [id,zh] of [[46,'今天来的人很多。'],[86,'我家在学校旁边。'],[214,'孩子们在公园里玩。'],[252,'我明天要去医院。']]) assert.equal(examples[id].zh,zh,'Weak example not replaced '+id);
class El{
  constructor(tag='div'){this.tagName=tag;this.children=[];this.value='';this.checked=false;this.hidden=false;this.attributes={};this.classList={add:()=>{}};this.textContent='';}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=children;}
  setAttribute(k,v){this.attributes[k]=v;}
  showModal(){this.open=true;}
  close(){this.open=false;}
}
const el={};const get=id=>el[id]||(el[id]=new El());
get('level').value='1';get('speed').value='1';
const audio=[];class AudioMock{
  constructor(src){this.src=src;audio.push(this);this.paused=false;}
  play(){return Promise.resolve();}
  pause(){this.paused=true;}
  removeAttribute(k){delete this[k];}
  load(){}
}
const status=()=>get('audioStatus').textContent;
const context={document:{getElementById:get,createElement:tag=>new El(tag),createTextNode:text=>({textContent:text}),addEventListener:()=>{}},localStorage:{getItem:()=>null,setItem:()=>{}},Audio:AudioMock,fetch:async url=>({ok:true,json:async()=>url.includes('hsk-data')?rows:examples}),setTimeout:()=>1,clearTimeout:()=>{},console};
vm.runInNewContext(fs.readFileSync('hsk.js','utf8'),context);
const descend=(e,p)=>[...(p(e)?[e]:[]),...(e.children||[]).flatMap(c=>descend(c,p))];
const buttons=()=>descend(get('cards'),e=>e.tagName==='button');
(async()=>{
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(get('cards').children.length,20);
  assert.equal(descend(get('cards'),e=>e.className==='example').length,20);
  for(const level of ['2','3','4','5']){
    get('level').value=level;get('level').onchange();
    assert.equal(descend(get('cards'),e=>e.className==='example').length,20,'Missing level '+level);
  }
  let b=buttons();b.find(b=>b.textContent==='🔊 ฟัง').onclick();const first=audio.at(-1);first.onplaying();
  b.find(b=>b.textContent==='🔊 ฟังประโยค').onclick();const second=audio.at(-1);assert(first.paused);assert(second.src.includes('example-audio/'));
  second.onplaying();const current=status();first.onerror();assert.equal(status(),current,'Stale audio error replaced current state');
  const count=audio.length;b.find(b=>b.textContent==='🔊 ฟังประโยค').onclick();assert.equal(audio.length,count,'Duplicate tap starts duplicate audio');
  get('speed').value='0.85';get('speed').onchange();assert.equal(second.playbackRate,.85);assert.equal(second.preservesPitch,true);
  get('stop').onclick();assert(second.paused);
  get('search').value='unlikely_no_word_!';get('search').oninput();assert.equal(get('cards').children.length,0);assert(get('startQuiz').disabled);
  get('search').value='';get('search').oninput();get('next').onclick();assert.equal(get('page').value,'1');
  console.log('PASS: 3600 examples, exact target highlights, Thai/pinyin, MP3 headers, all-level rendering, media switching, duplicate taps, slow mode, stop, empty search and pagination');
})().catch(e=>{console.error(e);process.exitCode=1;});
