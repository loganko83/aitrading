import { test, expect } from '@playwright/test';

test.describe('Production Site Test', () => {
  test('should load production site and check for errors', async ({ page }) => {
    const errors: string[] = [];
    const consoleMessages: string[] = [];

    // Capture console messages
    page.on('console', msg => {
      consoleMessages.push(`[${msg.type()}] ${msg.text()}`);
    });

    // Capture errors
    page.on('pageerror', error => {
      errors.push(`Page error: ${error.message}`);
    });

    page.on('requestfailed', request => {
      errors.push(`Request failed: ${request.url()} - ${request.failure()?.errorText}`);
    });

    // Navigate to production site
    console.log('Navigating to https://trendy.storydot.kr/trading...');
    const response = await page.goto('https://trendy.storydot.kr/trading/', {
      waitUntil: 'load',
      timeout: 30000
    });

    console.log('Response status:', response?.status());
    console.log('Response URL:', response?.url());

    // Take screenshot
    await page.screenshot({ path: 'production-site-screenshot.png', fullPage: true });

    // Check page title
    const title = await page.title();
    console.log('Page title:', title);

    // Check if page loaded
    const bodyText = await page.locator('body').textContent();
    console.log('Body text length:', bodyText?.length);

    // Print console messages
    console.log('\nConsole messages:');
    consoleMessages.forEach(msg => console.log(msg));

    // Print errors
    console.log('\nErrors:');
    errors.forEach(err => console.log(err));

    // Check for specific elements
    const hasLoginForm = await page.locator('form').count() > 0;
    console.log('Has form:', hasLoginForm);

    // Verify response status
    expect(response?.status()).toBeLessThan(400);
  });

  test('should test signup page on production', async ({ page }) => {
    const errors: string[] = [];

    page.on('pageerror', error => {
      errors.push(`Page error: ${error.message}`);
    });

    page.on('requestfailed', request => {
      errors.push(`Request failed: ${request.url()}`);
    });

    console.log('Navigating to signup page...');
    const response = await page.goto('https://trendy.storydot.kr/trading/signup/', {
      waitUntil: 'load',
      timeout: 30000
    });

    console.log('Signup page status:', response?.status());

    await page.screenshot({ path: 'production-signup-screenshot.png', fullPage: true });

    const title = await page.title();
    console.log('Signup page title:', title);

    // Check for form elements
    const nameInput = await page.getByLabel('Full Name').count();
    const emailInput = await page.getByLabel('Email').count();
    const passwordInput = await page.getByLabel('Password', { exact: true }).count();

    console.log('Name input:', nameInput);
    console.log('Email input:', emailInput);
    console.log('Password input:', passwordInput);

    console.log('\nErrors:', errors);

    expect(response?.status()).toBeLessThan(400);
  });

  test('should check API endpoints', async ({ request }) => {
    console.log('Testing /api/auth/session endpoint...');

    const sessionResponse = await request.get('https://trendy.storydot.kr/trading/api/auth/session');
    console.log('Session API status:', sessionResponse.status());
    console.log('Session API response:', await sessionResponse.text());

    // Session endpoint should return 200 with null user when not logged in
    expect(sessionResponse.status()).toBe(200);
  });
});
