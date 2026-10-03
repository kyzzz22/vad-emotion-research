const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({headless:true, ...(process.env.CHROME_CHANNEL ? {channel:process.env.CHROME_CHANNEL} : {})});
 const page=await browser.newPage(); const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8766/?short=1');
 await page.locator('#start').click();
 for(let b=0;b<4;b++){
  await page.locator('#rating').waitFor({state:'visible'});
  assert.equal(await page.locator('input[type=radio]:checked').count(),0);
  await page.locator('input[name=D_draft][value="5"]').check();
  await page.locator('#form button').click();
  for(const name of ['control','valence','arousal','difficulty','effort'])await page.locator(`input[name=${name}][value="6"]`).check();
  await page.locator('#form button').click();
 }
 await page.locator('#done').waitFor({state:'visible'});
 const downloading=page.waitForEvent('download');await page.locator('#download').click();const d=await downloading;
 const data=JSON.parse(fs.readFileSync(await d.path(),'utf8'));
 assert.equal(data.status,'completed');assert.equal(data.mode,'technical_demo_only');assert.equal(data.blocks.length,5);
 assert.equal(data.blocks[0].practice,true);assert.equal(data.blocks.slice(1).map(b=>b.condition).join(''),'CRRC');
 for(const b of data.blocks.slice(1)){assert.equal(Object.keys(b.ratings).length,6);assert.ok(b.samples.length>10);}
 await page.reload();await page.locator('#start').click();await page.locator('#stop').click();await page.locator('#done').waitFor({state:'visible'});
 await page.setViewportSize({width:390,height:844});await page.reload();
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 assert.deepEqual(errors,[]);
 console.log('PASS: practice + 4 blocks, staged required ratings, JSON export, stop, mobile overflow, no JS errors');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
