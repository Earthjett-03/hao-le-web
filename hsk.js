/* HSK vocabulary derived from the official November 2025 exam syllabus. */
const HskCore = (() => {
  const normalize = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
  const filterRows = (rows, level, query, unknown, known) => {
    const term = normalize(query);
    return rows.filter(r => (level === 'all' || r.level === Number(level)) && (!unknown || !known.has(r.id)) &&
      (!term || normalize([r.word, r.pinyin, r.thai].join(' ')).includes(term) || normalize(r.pinyin).replace(/\s/g,'').includes(term.replace(/\s/g,''))));
  };
  const shuffle = list => { const a = [...list]; for (let i=a.length-1;i>0;i--) { const j=Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]]; } return a; };
  const choices = (target, rows) => {
    const meanings = new Set([target.thai]); const options=[target.thai];
    for (const r of shuffle(rows)) { if (!meanings.has(r.thai)) { meanings.add(r.thai); options.push(r.thai); } if(options.length===4)break; }
    return shuffle(options);
  };
  return {normalize, filterRows, shuffle, choices};
})();
if (typeof module !== 'undefined') module.exports=HskCore;
if (typeof document !== 'undefined') (() => {
  const $=id=>document.getElementById(id), size=20;
  let rows=[], filtered=[], page=0, known=new Set(), player=null, audioId=null, request=0, timer;
  let quizItems=[], qi=0, score=0, answered=false, loading=false, examples={};
  try { const saved=JSON.parse(localStorage.getItem('hao-hsk2026-known')||'[]'); if(Array.isArray(saved))known=new Set(saved.filter(id=>Number.isInteger(id)&&id>=1&&id<=3600)); } catch {}
  const node=(tag,text,className)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(className)n.className=className;return n};
  function stop(){request++;clearTimeout(timer);if(player){player.pause();player.removeAttribute('src');player.load();player=null}audioId=null;}
  function play(row, example=false){
    const key=(example?'example:':'word:')+row.id;
    if(audioId===key&&player)return;
    stop();const serial=request;audioId=key;
    const a=new Audio(example?'./example-audio/'+row.audio+'.mp3':'./hsk-audio/'+row.id+'.mp3');player=a;a.playbackRate=Number($('speed').value);a.preservesPitch=true;
    $('audioStatus').textContent='กำลังโหลดเสียง '+row.word+'…';
    const fail=()=>{if(serial!==request)return;stop();$('audioStatus').textContent='เล่นเสียงไม่ได้ ตรวจอินเทอร์เน็ตแล้วแตะเพื่อลองอีกครั้ง';};
    timer=setTimeout(fail,15000);
    a.onplaying=()=>{if(serial===request){clearTimeout(timer);$('audioStatus').textContent='กำลังอ่าน '+row.word+' · '+row.pinyin;}};
    a.onended=()=>{if(serial===request){stop();$('audioStatus').textContent='อ่านจบแล้ว แตะเพื่อฟังซ้ำได้';}};
    a.onerror=fail;a.play().catch(fail);
  }
  function saveKnown(){try{localStorage.setItem('hao-hsk2026-known',JSON.stringify([...known]));}catch{$('audioStatus').textContent='เครื่องนี้บันทึกไม่ได้ แต่ยังเรียนต่อในรอบนี้ได้';}}
  function render(){
    filtered=HskCore.filterRows(rows,$('level').value,$('search').value,$('unknownOnly').checked,known);
    const totalPages=Math.max(1,Math.ceil(filtered.length/size));page=Math.max(0,Math.min(page,totalPages-1));
    const current=filtered.slice(page*size,(page+1)*size);
    $('cards').replaceChildren();
    current.forEach(r=>{
      const card=node('article',undefined,'card'+(known.has(r.id)?' known':''));
      card.append(node('span','HSK '+r.level+' · #'+r.id,'meta'),node('strong',r.word,'hanzi'),node('div',r.pinyin,'pinyin'),node('div',r.thai,'meaning'));
      if(r.pos)card.append(node('span',r.pos,'meta'));
      const actions=node('div',undefined,'card-actions');const listen=node('button','🔊 ฟัง');listen.setAttribute('aria-label','ฟัง '+r.word);listen.onclick=()=>play(r);
      const mark=node('button',known.has(r.id)?'✓ จำได้แล้ว':'จำได้แล้ว','secondary');mark.setAttribute('aria-pressed',String(known.has(r.id)));mark.onclick=()=>{known.has(r.id)?known.delete(r.id):known.add(r.id);saveKnown();render();};
      actions.append(listen,mark);card.append(actions);$('cards').append(card);
      const ex=examples[r.id];
      if(ex){
        const block=node('section',undefined,'example');block.setAttribute('aria-label','ประโยคตัวอย่างของ '+r.word);
        block.append(node('span','ประโยคตัวอย่าง','example-label'));
        const chinese=node('p',undefined,'example-zh');chinese.lang='zh-CN';
        const at=Number.isInteger(ex.start)&&ex.zh.slice(ex.start,ex.start+r.word.length)===r.word?ex.start:ex.zh.indexOf(r.word);
        if(at>=0)chinese.append(document.createTextNode(ex.zh.slice(0,at)),node('mark',r.word),document.createTextNode(ex.zh.slice(at+r.word.length)));
        else chinese.textContent=ex.zh;
        const pinyin=node('p',ex.pinyin,'example-pinyin');pinyin.lang='zh-Latn';
        const hear=node('button','🔊 ฟังประโยค','secondary');hear.setAttribute('aria-label','ฟังประโยค '+ex.zh);
        hear.onclick=()=>play({id:ex.audio,audio:ex.audio,word:ex.zh,pinyin:ex.pinyin},true);
        block.append(chinese,pinyin,node('p',ex.thai,'example-thai'),hear);card.append(block);
      }
    });
    $('page').replaceChildren(...Array.from({length:totalPages},(_,i)=>{const o=node('option',String(i+1));o.value=String(i);return o}));$('page').value=String(page);
    $('pageSummary').textContent='/ '+totalPages+' ชุด · '+filtered.length.toLocaleString('th-TH')+' รายการ';
    $('prev').disabled=page===0;$('next').disabled=page===totalPages-1;$('page').disabled=filtered.length===0;
    $('progress').textContent='จำได้ '+known.size.toLocaleString('th-TH')+' / 3,600 รายการ';
    $('loadStatus').textContent=filtered.length?'':'ไม่พบคำศัพท์ ลองเปลี่ยนคำค้นหรือระดับ';$('loadStatus').hidden=filtered.length>0;
    $('startQuiz').disabled=current.length===0;
  }
  function question(){
    answered=false;$('answers').replaceChildren();$('feedback').textContent='';$('nextQuestion').hidden=true;
    $('quizCount').textContent='ข้อ '+(qi+1)+' / '+quizItems.length;
    const target=quizItems[qi];$('question').textContent=target.word+' ('+target.pinyin+') แปลว่าอะไร?';
    HskCore.choices(target,rows).forEach(value=>{
      const button=node('button',value);
      button.onclick=()=>{if(answered)return;answered=true;const correct=value===target.thai;if(correct)score++;
        for(const b of $('answers').children){b.disabled=true;if(b.textContent===target.thai)b.classList.add('correct');}
        if(!correct)button.classList.add('wrong');
        $('feedback').textContent=correct?'ถูกต้อง!':'คำตอบในคลังศัพท์: '+target.thai;
        $('nextQuestion').textContent=qi===quizItems.length-1?'ดูผลคะแนน':'ข้อต่อไป →';$('nextQuestion').hidden=false;
      };$('answers').append(button);
    });
  }
  $('startQuiz').onclick=()=>{stop();quizItems=HskCore.shuffle(filtered.slice(page*size,(page+1)*size)).slice(0,10);if(!quizItems.length)return;qi=0;score=0;question();$('quiz').showModal();};
  $('nextQuestion').onclick=()=>{if(!answered||$('nextQuestion').hidden)return;$('nextQuestion').hidden=true;qi++;
    if(qi<quizItems.length){question();return;}
    $('quizCount').textContent='ทบทวนเสร็จแล้ว';$('question').textContent='ได้ '+score+' / '+quizItems.length+' คะแนน';$('answers').replaceChildren();$('feedback').textContent='กลับไปฟังและทบทวนคำที่ยังไม่แม่น แล้วฝึกชุดนี้อีกครั้งได้';
  };
  $('closeQuiz').onclick=()=>$('quiz').close();
  $('level').onchange=()=>{stop();page=0;render();};$('unknownOnly').onchange=()=>{page=0;render();};
  $('search').oninput=()=>{page=0;render();};$('page').onchange=()=>{stop();page=Number($('page').value);render();};
  $('prev').onclick=()=>{if(page===0)return;stop();page--;render();};$('next').onclick=()=>{if((page+1)*size>=filtered.length)return;stop();page++;render();};
  $('stop').onclick=()=>{stop();$('audioStatus').textContent='หยุดเสียงแล้ว';};$('speed').onchange=()=>{if(player)player.playbackRate=Number($('speed').value);};
  document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
  async function load(){
    if(loading)return;loading=true;$('loadStatus').textContent='กำลังโหลดคลังศัพท์…';
    try{const response=await fetch('./hsk-data.json?v=corrections-1');if(!response.ok)throw Error('Load failed');const data=await response.json();
      if(!Array.isArray(data)||data.length!==3600||data.some(r=>!r.word||!r.pinyin||!r.thai))throw Error('Incomplete data');rows=data;render();
    }catch{$('loadStatus').replaceChildren(node('span','โหลดคลังศัพท์ไม่ได้ '));const retry=node('button','ลองอีกครั้ง');retry.onclick=load;$('loadStatus').append(retry);}
    finally{loading=false;}
  }
  load();
  async function loadExamples(){
    const status=$('exampleStatus');
    try{
      const response=await fetch('./hsk-examples.json?v=corrections-1');if(!response.ok)throw Error('Examples unavailable');
      const data=await response.json();
      if(Object.keys(data).length!==3600||Array.from({length:3600},(_,i)=>data[i+1]).some(e=>!e||!e.zh||!e.pinyin||!e.thai||!/^[a-f0-9]{16}$/.test(e.audio)))throw Error('Invalid examples');
      examples=data;status.textContent='HSK 1–5 · ทุกคำมีประโยคตัวอย่าง พร้อมพินอิน คำแปลไทย และเสียง รวม 3,600 คำ';
      if(rows.length)render();
    }catch{
      status.replaceChildren(node('span','โหลดประโยคตัวอย่างไม่สำเร็จ แต่ยังท่องศัพท์ได้ '));
      const retry=node('button','โหลดตัวอย่างอีกครั้ง','secondary');retry.onclick=()=>{retry.disabled=true;loadExamples();};status.append(retry);
    }
  }
  loadExamples();
})();
