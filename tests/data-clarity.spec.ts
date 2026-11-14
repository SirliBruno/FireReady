import {test,expect} from '@playwright/test';
test('overview explains that research observations are loaded',async({page})=>{
 await page.goto('/#command');
 await expect(page.getByRole('region',{name:'مصدر البيانات'})).toContainText('البيانات البحثية محمّلة');
 await expect(page.getByRole('region',{name:'مصدر البيانات'})).toContainText('1146');
 await expect(page.getByRole('link',{name:'شاهد المشاهدات على الخريطة'})).toBeVisible();
});
