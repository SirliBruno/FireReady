import {test,expect} from '@playwright/test';
test('built production assets and local map support the live solver',async({page})=>{
 await page.route('https://tiles.openfreemap.org/**',route=>route.abort());await page.route('https://fonts.googleapis.com/**',route=>route.abort());await page.route('https://fonts.gstatic.com/**',route=>route.abort());await page.goto('/#simulator',{waitUntil:'domcontentloaded'});await page.getByRole('button',{name:'جرّب سيناريو توضيحي'}).click();await expect(page.getByText('حصة الطلب التاريخي المغطاة: 87.0%')).toBeVisible();
 const response=await page.request.get('/data/maui-boundary.geojson');expect(response.ok()).toBe(true);expect((await response.json()).type).toBe('FeatureCollection');
 const planning=await page.request.get('/data/planning/maui.json');expect((await planning.json()).grid).toHaveLength(2039);await page.reload({waitUntil:'domcontentloaded'});await expect(page.getByLabel('نموذج التخطيط')).toHaveValue('annual');
});
