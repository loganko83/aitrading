import { test, expect } from '@playwright/test';

test.describe('Signup Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to signup page with basePath
    await page.goto('/trading/signup');
  });

  test('should display signup form correctly', async ({ page }) => {
    // Check page title
    await expect(page.getByRole('heading', { name: 'Create Account' })).toBeVisible();

    // Check form fields are present
    await expect(page.getByLabel('Full Name')).toBeVisible();
    await expect(page.getByLabel('Email')).toBeVisible();
    await expect(page.getByLabel('Password', { exact: true })).toBeVisible();
    await expect(page.getByLabel('Confirm Password')).toBeVisible();

    // Check submit button
    await expect(page.getByRole('button', { name: 'Create Account' })).toBeVisible();

    // Check terms and privacy links
    await expect(page.getByText('Terms of Service')).toBeVisible();
    await expect(page.getByText('Privacy Policy')).toBeVisible();
  });

  test('should show validation errors for invalid inputs', async ({ page }) => {
    // Click submit without filling any fields
    await page.getByRole('button', { name: 'Create Account' }).click();

    // Wait for validation errors
    await expect(page.getByText('Name must be at least 2 characters')).toBeVisible();
    await expect(page.getByText('Invalid email address')).toBeVisible();
  });

  test('should show error when passwords do not match', async ({ page }) => {
    // Fill form with mismatched passwords
    await page.getByLabel('Full Name').fill('Test User');
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password', { exact: true }).fill('password123');
    await page.getByLabel('Confirm Password').fill('password456');

    // Submit form
    await page.getByRole('button', { name: 'Create Account' }).click();

    // Check for password mismatch error
    await expect(page.getByText("Passwords don't match")).toBeVisible();
  });

  test('should show error for short password', async ({ page }) => {
    // Fill form with short password
    await page.getByLabel('Full Name').fill('Test User');
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password', { exact: true }).fill('pass');
    await page.getByLabel('Confirm Password').fill('pass');

    // Submit form
    await page.getByRole('button', { name: 'Create Account' }).click();

    // Check for short password error
    await expect(page.getByText('Password must be at least 8 characters')).toBeVisible();
  });

  test('should successfully submit valid signup form', async ({ page }) => {
    // Generate unique email for test
    const timestamp = Date.now();
    const testEmail = `test-${timestamp}@example.com`;

    // Fill form with valid data
    await page.getByLabel('Full Name').fill('Logan KO');
    await page.getByLabel('Email').fill(testEmail);
    await page.getByLabel('Password', { exact: true }).fill('SecurePassword123!');
    await page.getByLabel('Confirm Password').fill('SecurePassword123!');

    // Submit form
    await page.getByRole('button', { name: 'Create Account' }).click();

    // Wait for loading state
    await expect(page.getByRole('button', { name: 'Creating account...' })).toBeVisible();

    // Wait for redirect or success (may go to OTP verification or login)
    // This will depend on your backend implementation
    await page.waitForURL(/\/(verify-otp|login)/, { timeout: 10000 });

    // Verify we're no longer on signup page
    expect(page.url()).not.toContain('/signup');
  });

  test('should navigate to login page when clicking Sign In', async ({ page }) => {
    // Click "Sign In" button
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Verify navigation to login page
    await expect(page).toHaveURL('/trading/login');
  });

  test('should have working Terms and Privacy links', async ({ page }) => {
    // Check Terms of Service link
    const termsLink = page.getByRole('link', { name: 'Terms of Service' });
    await expect(termsLink).toBeVisible();
    expect(await termsLink.getAttribute('href')).toContain('/terms');

    // Check Privacy Policy link
    const privacyLink = page.getByRole('link', { name: 'Privacy Policy' });
    await expect(privacyLink).toBeVisible();
    expect(await privacyLink.getAttribute('href')).toContain('/privacy');
  });

  test('should handle API error gracefully', async ({ page }) => {
    // Fill form with demo email (which should trigger conflict)
    await page.getByLabel('Full Name').fill('Demo User');
    await page.getByLabel('Email').fill('demo@example.com');
    await page.getByLabel('Password', { exact: true }).fill('Password123!');
    await page.getByLabel('Confirm Password').fill('Password123!');

    // Submit form
    await page.getByRole('button', { name: 'Create Account' }).click();

    // Wait for error message (may be conflict or other error)
    await page.waitForSelector('text=/error|already exists|failed/i', { timeout: 10000 });
  });

  test('should verify basePath API calls are working', async ({ page }) => {
    // Listen to network requests
    const apiRequests: string[] = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiRequests.push(request.url());
      }
    });

    // Fill and submit form
    await page.getByLabel('Full Name').fill('Test User');
    await page.getByLabel('Email').fill(`test-${Date.now()}@example.com`);
    await page.getByLabel('Password', { exact: true }).fill('Password123!');
    await page.getByLabel('Confirm Password').fill('Password123!');
    await page.getByRole('button', { name: 'Create Account' }).click();

    // Wait a bit for API call
    await page.waitForTimeout(2000);

    // Verify API was called with correct basePath
    const signupRequest = apiRequests.find(url => url.includes('/api/auth/signup'));
    expect(signupRequest).toBeTruthy();
    expect(signupRequest).toContain('/trading/api/auth/signup');
  });
});
