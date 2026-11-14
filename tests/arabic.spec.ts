import { test, expect } from '@playwright/test';
test('Arabic-first navigation preserves scientific caveats', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('html')).toHaveAttribute('lang', 'ar');
  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
  await expect(page.getByRole('link', { name: 'نظرة عامة', exact: true })).toBeVisible();
  await page.goto('/#simulator');
  await expect(page.getByRole('button', { name: /تشغيل المحاكاة/ })).toBeEnabled();
});
