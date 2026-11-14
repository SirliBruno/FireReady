import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {optimizeCoverage} from '../src/services/optimizer';
test('hero scenario and simultaneous incidents use actual assignments',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/#simulator');await expect(page.getByLabel('نموذج التخطيط')).toHaveValue('annual');
 await page.getByRole('button',{name:'جرّب سيناريو توضيحي'}).click();
 await expect(page.getByText('حصة الطلب التاريخي المغطاة: 87.0%')).toBeVisible();
 const d=JSON.parse(readFileSync('public/data/planning/maui.json','utf8'));const r=optimizeCoverage(d.costs_km,d.monthly_weights['8'],3,10);const s=r.selected[0];const cells=d.costs_km[s].map((distance:number,i:number)=>({distance,i})).sort((a:{distance:number},b:{distance:number})=>a.distance-b.distance).slice(0,2);
 for(const c of cells){await page.getByLabel('خلية الحادث',{exact:true}).selectOption(String(c.i));await page.getByRole('button',{name:'إضافة الحادث',exact:true}).click();}
 await expect(page.locator('.incidents-panel')).toContainText('من 2');
 await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:'docs/screenshots/sprint06-incidents.png',fullPage:true});await page.getByRole('button',{name:'مسح الحوادث',exact:true}).click();await expect(page.locator('.incidents-panel')).toContainText('من 0');
 await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:'docs/screenshots/sprint06-simulator.png',fullPage:true});
 await page.getByLabel('عدد المركبات الافتراضي').fill('0');await page.getByRole('button',{name:'تشغيل المحاكاة',exact:true}).click();await expect(page.getByText('0 مركبة افتراضية')).toHaveCount(2);
 await page.goto('/#science');expect(errors).toEqual([]);
});
test('presentation keyboard and mobile layout',async({page})=>{const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.setViewportSize({width:390,height:844});await page.goto('/#presentation');const hook=await page.locator('.pitch-hook .map-wrap').boundingBox();expect(hook?.width).toBeGreaterThan(200);await page.keyboard.press('ArrowLeft');await expect(page.locator('.presentation>strong')).toHaveText('قصة ماوي');for(let i=0;i<4;i++)await page.getByRole('button',{name:'التالي',exact:true}).click();await expect(page.locator('.presentation>strong')).toHaveText('حل FireReady');await page.getByRole('button',{name:'جرّب سيناريو توضيحي'}).click();await expect(page.getByText('حصة الطلب التاريخي المغطاة: 87.0%')).toBeVisible();await page.getByRole('button',{name:'التالي',exact:true}).click();await expect(page.getByText('حصة الطلب التاريخي المغطاة: 87.0%')).toBeVisible();await page.getByRole('button',{name:'التالي',exact:true}).click();await expect(page.locator('.presentation>strong')).toHaveText('النتائج والقيود');expect(errors).toEqual([]);await page.goto('/#simulator');await page.getByRole('button',{name:'جرّب سيناريو توضيحي'}).click();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:'docs/screenshots/sprint06-mobile.png',fullPage:true})});

