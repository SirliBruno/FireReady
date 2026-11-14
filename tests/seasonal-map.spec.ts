import {test,expect} from '@playwright/test';
test('seasonal map updates using precomputed Maui observations',async({page})=>{
 await page.goto('/#seasonal');
 await expect(page.getByText('نشاط تاريخي مرصود · التغطية غير معروفة')).toBeVisible();
 await expect(page.locator('.seasonal-top')).toContainText('167');
 await page.getByRole('button',{name:'فبراير',exact:true}).click();
 await expect(page.locator('.seasonal-top')).toContainText('45');
 await page.getByLabel('سنة الخريطة الموسمية').selectOption('2023');
 await expect(page.getByRole('button',{name:'فبراير',exact:true})).toHaveAttribute('aria-pressed','true');
 await expect(page.locator('.research-map[aria-label="خريطة النشاط التاريخي الموسمي"]')).toBeVisible();
});
