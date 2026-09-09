const assert=require('node:assert/strict');
const fs=require('node:fs');
const core=require('./hsk.js');
const rows=JSON.parse(fs.readFileSync('hsk-data.json','utf8'));
assert.equal(rows.length,3600);
assert.deepEqual(rows.map(r=>r.id),Array.from({length:3600},(_,i)=>i+1));
assert.deepEqual([1,2,3,4,5].map(l=>rows.filter(r=>r.level===l).length),[300,200,500,1000,1600]);
assert(rows.every(r=>r.word&&r.pinyin&&r.thai));
assert.equal(core.filterRows(rows,'1','',false,new Set()).length,300);
assert.equal(core.filterRows(rows,'all','',true,new Set([1,2])).length,3598);
assert(core.filterRows(rows,'1','nihao',false,new Set()).some(r=>r.word==='你好'));
assert(core.filterRows(rows,'all','สวัสดี',false,new Set()).some(r=>r.word==='你好'));
for(const target of rows){const answers=core.choices(target,rows.slice(0,100));assert(answers.includes(target.thai));assert.equal(new Set(answers).size,answers.length);assert.equal(answers.length,4);
  const bytes=fs.readFileSync('hsk-audio/'+target.id+'.mp3');assert(bytes.length>1000);assert(bytes.subarray(0,3).toString()==='ID3'||(bytes[0]===255&&(bytes[1]&224)===224));}
new Function(fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*?)<\/script>/)[1]);
console.log('PASS: 3600 IDs, level counts, data completeness, Chinese/Thai/pinyin search, progress filters, unique quiz choices, 3600 MP3 headers and app syntax');
