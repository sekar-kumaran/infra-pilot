import { test, expect } from '@playwright/test';

test.describe('InfraPilot E2E Workflow', () => {
  test('Complete Operational Workflow', async ({ page }) => {
    // 1. Login
    await page.goto('/login');
    await page.fill('input[type="email"]', 'admin@example.com');
    await page.fill('input[type="password"]', 'admin123'); // Assuming default admin credentials
    await page.click('button[type="submit"]');

    // 2. Dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');

    // 3. Infrastructure
    await page.click('text=Infrastructure');
    await expect(page).toHaveURL('/infrastructure/environments');
    await expect(page.locator('h1')).toContainText('Environments');

    // 4. Integrations
    await page.click('text=Integrations');
    await expect(page).toHaveURL('/integrations');
    await expect(page.locator('h1')).toContainText('Integrations');

    // 5. Events
    await page.click('text=Events');
    await expect(page).toHaveURL('/events');
    await expect(page.locator('h1')).toContainText('Events');

    // 6. Alerts
    await page.click('text=Alerts');
    await expect(page).toHaveURL('/alerts');
    await expect(page.locator('h1')).toContainText('Alerts');

    // 7. Incidents
    await page.click('text=Incidents');
    await expect(page).toHaveURL('/incidents');
    await expect(page.locator('h1')).toContainText('Incidents');

    // 8. Incident Timeline (View details)
    const viewButton = page.locator('a:has-text("View")').first();
    if (await viewButton.isVisible()) {
      await viewButton.click();
      await expect(page.locator('h1')).toContainText('Incident Details');
      await expect(page.locator('text=Timeline')).toBeVisible();
    }

    // 9. Automation
    await page.click('text=Automation');
    await expect(page).toHaveURL('/automation/playbooks');
    await expect(page.locator('h1')).toContainText('Playbooks');

    // 10. Approvals (Part of automation)
    await page.goto('/automation/approvals');
    await expect(page.locator('h1')).toContainText('Approvals');

    // 11. Executions
    await page.goto('/automation/executions');
    await expect(page.locator('h1')).toContainText('Automation Executions');

    // 12. Policies (Policy Evaluation context)
    await page.click('text=Policies');
    await expect(page).toHaveURL('/policies');
    await expect(page.locator('h1')).toContainText('Policies');

    // 13. Audit
    await page.click('text=Audit Logs');
    await expect(page).toHaveURL('/audit');
    await expect(page.locator('h1')).toContainText('Audit Logs');
  });
});
