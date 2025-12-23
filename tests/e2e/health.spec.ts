import { test, expect } from '../support/fixtures';

test.describe('Health Check', () => {
  test('backend API is healthy', async ({ request, apiUrl }) => {
    const response = await request.get(`${apiUrl}/api/health`);
    expect(response.ok()).toBeTruthy();
    expect(await response.json()).toEqual({ status: 'healthy' });
  });

  test('frontend loads successfully', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/BookBrain|Vite/);
  });
});
