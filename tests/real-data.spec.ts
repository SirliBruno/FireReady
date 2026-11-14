import {test,expect} from '@playwright/test';
test('supplied research observations appear in maps and seasonal chart',async({page})=>{
 await page.goto('/#harmonization');
 await expect(page.getByText('معاينة بحثية · لم يُتحقق من المصدر بصورة مستقلة')).toBeVisible();
 await expect(page.locator('.research-selection')).toContainText('مشاهدة معروضة');
 await page.goto('/#seasonal');
 await expect(page.getByText('المجموعة المرجعية تستبعد NOAA-20.',{exact:false})).toBeVisible();
 await expect(page.getByLabel('السنة')).toBeVisible();
 await page.getByLabel('السنة').selectOption('2023');
 await expect(page.locator('.recharts-bar-rectangle').first()).toBeVisible();
});
