'use strict';
const $=id=>document.getElementById(id);
const short=new URLSearchParams(location.search).get('short')==='1';
const duration=short?3000:60000;
const items=[
 ['D_draft','直前の区間で、あなたはどの程度、周囲に支配されている／自分が主導していると感じましたか。','周囲に支配されている','自分が主導している'],
 ['control','この課題では、自分の操作によって結果を変えられると感じましたか。','全く感じなかった','強く感じた'],
 ['valence','直前の区間で、どの程度快い気持ちでしたか。','非常に不快','非常に快'],
 ['arousal','直前の区間で、どの程度気持ちが高ぶっていましたか。','非常に落ち着いていた','非常に高ぶっていた'],
 ['difficulty','直前の区間の課題は、どの程度難しかったですか。','全く難しくなかった','非常に難しかった'],
 ['effort','直前の区間で、どの程度努力しましたか。','全く努力しなかった','非常に努力した']
];
let data,block=-1,current=null,timer=null,pressed=new Set(),pendingRating=null;
function event(type,detail={}){if(data)data.events.push({type,t_ms:performance.now()-data.start_clock,...detail});}
function exportData(){const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`control-demo-${data.id}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('download').onclick=exportData;
function finish(aborted){clearInterval(timer);current=null;pressed.clear();data.status=aborted?'aborted':'completed';event(data.status);$('task').hidden=true;$('rating').hidden=true;$('done').hidden=false;$('download').hidden=false;$('summary').textContent=aborted?'中止しました。途中の記録も保存できます。':'練習と4区間の記録を保存できます。';}
function startBlock(){block++;pendingRating=null;pressed.clear();if(block>=4){finish(false);return;}
 const isPractice=block===-1;
 const condition=isPractice?'C':data.order[block];
 current={index:block,practice:isPractice,condition,started:performance.now(),samples:[],ratings:null};data.blocks.push(current);
 $('rating').hidden=true;$('task').hidden=false;$('heading').textContent=isPractice?'練習（操作が反映されます）':`区間 ${block+1} / 4`;
 let last=performance.now(),x=.5; event('block_start',{block,condition,practice:isPractice});
 timer=setInterval(()=>{if(!current)return;const now=performance.now(),elapsed=now-current.started,dt=Math.min((now-last)/1000,.1);last=now;
 const input=(pressed.has('right')?1:0)-(pressed.has('left')?1:0);
 if(condition==='C')x=Math.max(.03,Math.min(.97,x+input*dt*.6+Math.sin(elapsed/430)*dt*.12));
 else x=.5+.36*Math.sin(elapsed/1100); // synthetic replay: deliberately NOT matched or yoked
 current.samples.push({t_ms:Math.round(elapsed),x,input,in_target:x>=.4&&x<=.6});$('dot').style.left=`${x*100}%`;
 const limit=isPractice?(short?1000:10000):duration;$('remaining').textContent=`残り ${Math.max(0,Math.ceil((limit-elapsed)/1000))} 秒`;
 if(elapsed>=limit){clearInterval(timer);current.ended_ms=elapsed;pendingRating=current;current=null;pressed.clear();event('block_end',{block});if(isPractice)startBlock();else showRating();}
 },50);
}
function showRating(){ $('task').hidden=true;$('rating').hidden=false;const form=$('form');form.replaceChildren();let stage=0;
 function showItems(list){for(const [name,prompt,low,high] of list){const field=document.createElement('fieldset'),legend=document.createElement('legend');legend.textContent=prompt;field.append(legend);const anchors=document.createElement('p');anchors.className='anchors';anchors.textContent=`1：${low} ／ 9：${high}`;field.append(anchors);for(let n=1;n<=9;n++){const label=document.createElement('label'),input=document.createElement('input');input.type='radio';input.name=name;input.value=n;input.required=true;label.append(input,document.createTextNode(String(n)));field.append(label);}form.append(field);}}
 showItems(items.slice(0,1));const next=document.createElement('button');next.type='submit';next.textContent='次へ';form.append(next);
 form.onsubmit=e=>{e.preventDefault();const answers=Object.fromEntries([...new FormData(form)].map(([k,v])=>[k,Number(v)]));pendingRating.ratings={...pendingRating.ratings,...answers};if(stage===0){stage=1;form.replaceChildren();showItems(items.slice(1));next.textContent='回答を記録して続ける';form.append(next);}else{event('ratings',{block,values:pendingRating.ratings});startBlock();}};
}
$('start').onclick=()=>{if(!/^[A-Za-z0-9_-]{1,32}$/.test($('pid').value)){$('notice').textContent='IDは半角英数字・ハイフン・アンダースコアで入力してください。';return;}
 data={version:'0.1',mode:'technical_demo_only',measurement:'custom_Japanese_draft_NOT_SAM',short_mode:short,id:$('pid').value,order:$('order').value,started_at:new Date().toISOString(),start_clock:performance.now(),status:'running',blocks:[],events:[],limitations:['synthetic replay not outcome matched','no validated Japanese SAM','not for research collection']};$('setup').hidden=true;$('download').hidden=false;block=-2;startBlock();};
$('stop').onclick=()=>finish(true);
for(const [id,direction] of [['left','left'],['right','right']]){const el=$(id);el.onpointerdown=e=>{el.setPointerCapture(e.pointerId);pressed.add(direction);event('input_down',{direction});};for(const kind of ['pointerup','pointercancel','lostpointercapture'])el.addEventListener(kind,()=>pressed.delete(direction));}
window.addEventListener('keydown',e=>{if(current&&['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();pressed.add(e.key==='ArrowLeft'?'left':'right');}});
window.addEventListener('keyup',e=>pressed.delete(e.key==='ArrowLeft'?'left':e.key==='ArrowRight'?'right':''));
window.addEventListener('blur',()=>{pressed.clear();if(current){event('focus_lost');finish(true);}});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&current){event('page_hidden');finish(true);}});
window.addEventListener('beforeunload',e=>{if(data&&data.status==='running'){e.preventDefault();e.returnValue='';}});
