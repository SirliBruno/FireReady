import { test } from '@playwright/test';
test('capture Arabic views', async ({ page }) => {
 await page.setViewportSize({width:1440,height:900});
 for (const [hash,name] of [['landing','arabic-landing'],['command','arabic-overview'],['harmonization','arabic-exploration']]) { await page.goto('/#'+hash); await page.waitForTimeout(1800); await page.screenshot({path:'docs/screenshots/'+name+'.png',fullPage:true}); }
 await page.setViewportSize({width:390,height:844}); await page.goto('/#command'); await page.waitForTimeout(1200); await page.screenshot({path:'docs/screenshots/arabic-mobile.png',fullPage:true});
});
