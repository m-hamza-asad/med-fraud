import { expect, test } from '@playwright/test'
import path from 'node:path'

async function login(page: import('@playwright/test').Page) {
  await page.goto('/')
  await page.getByLabel('Username').fill('admin')
  await page.getByLabel('Password').fill('E2e-Admin-Password-2026!')
  await page.getByRole('button', { name: 'Open workspace' }).click()
  await expect(page.getByRole('heading', { name: 'Payment-integrity picture' })).toBeVisible()
}

test('catalogue, preview/commit, and graph workflow', async ({ page }) => {
  const consoleErrors: string[] = []
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()) })
  await login(page)
  consoleErrors.length = 0 // the expected unauthenticated session probe returns 401 before sign-in
  await page.getByRole('link', { name: 'Rules & configuration' }).click()
  await expect(page.getByText('164', { exact: true }).first()).toBeVisible()
  await page.getByLabel('Search rules').fill('ENT-01-R01')
  await page.getByRole('row').filter({ hasText: 'ENT-01-R01' }).getByRole('link').click()
  await expect(page.getByText('ENT-01-R01', { exact: true }).first()).toBeVisible()
  await page.getByText('Evaluation contract and technical traceability').click()
  await expect(page.getByRole('heading', { name: 'Evaluation contract' })).toBeVisible()

  await page.getByRole('link', { name: 'Upload & validation' }).click()
  await page.locator('input[type=file]').setInputFiles(path.resolve('../../data/demo/canonical-demo-claims.csv'))
  await page.getByLabel('Analysis date').fill('2026-09-15')
  await page.getByRole('button', { name: 'Validate and preview' }).click()
  const commit = page.getByRole('button', { name: /Commit .* reviewed rows/ })
  if (await commit.isVisible()) await commit.click()
  await expect(page.getByRole('heading', { name: 'COMMITTED' })).toBeVisible()

  const run = await page.evaluate(async () => {
    const batches = await fetch('/api/v1/imports', { credentials: 'include' }).then(response => response.json())
    const started = await fetch('/api/v1/evaluations', { method: 'POST', credentials: 'include',
      headers: { 'content-type': 'application/json', 'x-csrf-token': sessionStorage.getItem('csrf') ?? '' },
      body: JSON.stringify({ batch_id: batches[0].id, analysis_date: '2026-09-15' }) }).then(response => response.json())
    for (let attempt = 0; attempt < 100; attempt++) {
      const current = await fetch(`/api/v1/evaluations/${started.id}`, { credentials: 'include' }).then(response => response.json())
      if (current.status.startsWith('COMPLETED') || current.status === 'FAILED') return current
      await new Promise(resolve => setTimeout(resolve, 100))
    }
    throw new Error('Evaluation did not finish')
  })
  expect(run.progress.errors).toBe(0)
  expect(run.progress.rules).toBe(149)

  await page.goto('/claims/1')
  await expect(page.getByRole('heading', { name: 'DEMO-FLAG-001' })).toBeVisible()
  await expect(page.getByText('Review needed', { exact: true })).toBeVisible()
  await expect(page.getByText('Limited assessment', { exact: true })).toBeVisible()
  await expect(page.getByText(/not confirmed loss, overpayment, or recoverable value/).first()).toBeVisible()

  await page.getByRole('link', { name: 'Networks' }).click()
  await page.getByRole('link', { name: 'Review relationships in NET-DEMO-01' }).click()
  await expect(page.locator('.graph-panel')).toHaveAttribute('aria-hidden', 'true')
  await expect(page.locator('.graph-panel .react-flow__node')).toHaveCount(2)
  await expect(page.locator('.graph-panel .react-flow__edge')).toHaveCount(1)
  await page.locator('.graph-panel').scrollIntoViewIfNeeded()
  await expect(page.locator('.graph-panel .react-flow__node').first()).toBeInViewport()
  await expect(page.getByRole('heading', { name: 'Each line connects a provider to a member with a supporting claim' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Provider–member relationships and supporting claims' })).toBeVisible()
  await expect(page).toHaveScreenshot('network-graph-desktop.png', { fullPage: true, animations: 'disabled' })
  expect(consoleErrors).toEqual([])
})

test('keyboard focus, labels, landmark, and responsive visual smoke', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('main')).toHaveCount(1)
  await expect(page.getByLabel('Username')).toBeVisible()
  await expect(page.getByLabel('Password')).toHaveAttribute('type', 'password')
  await page.keyboard.press('Tab')
  await expect(page.getByLabel('Username')).toBeFocused()
  await expect(page).toHaveScreenshot('login-desktop.png', { fullPage: true, animations: 'disabled' })
  await page.setViewportSize({ width: 390, height: 844 })
  await expect(page).toHaveScreenshot('login-mobile.png', { fullPage: true, animations: 'disabled' })
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)
  expect(overflow).toBe(false)
})
