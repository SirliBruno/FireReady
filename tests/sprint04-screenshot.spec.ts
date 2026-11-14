import {test} from '@playwright/test';
test('capture seasonal sprint desktop and mobile',async({page})=>{
 for(const [width,height,name] of [[1440,900,'sprint04-seasonal-desktop'],[390,844,'sprint04-seasonal-mobile']] as const){await page.setViewportSize({width,height});await page.goto('/#seasonal');await page.getByText('نشاط تاريخي مرصود · التغطية غير معروفة').waitFor();await page.waitForTimeout(1200);await page.screenshot({path:`docs/screenshots/${name}.png`,fullPage:true});}
});
