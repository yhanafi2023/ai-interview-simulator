import { expect, test } from '@playwright/test'

test('a user can answer a question and receive feedback', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Email').fill('jack@example.com')
  await page.getByLabel('Password').fill('password123')
  await page.getByRole('button', { name: 'Log in' }).click()
  await expect(page).toHaveURL(/\/dashboard/)

  await page.getByLabel('Type').selectOption('behavioral')
  await page.getByRole('button', { name: 'Start interview' }).click()

  await expect(page).toHaveURL(/\/interview\//)

  await page
    .getByLabel('Your answer')
    .fill(
      'I disagreed with a teammate about whether to add a caching layer before we had measured ' +
        'the actual latency. I asked to spend an afternoon instrumenting the endpoint first. ' +
        'The data showed the bottleneck was a missing database index, not repeated computation, ' +
        'so we fixed the index and skipped the cache entirely. I learned to argue with numbers ' +
        'rather than opinions, and my teammate and I agreed on the outcome quickly once we had them.',
    )

  await page.getByRole('button', { name: 'Submit answer' }).click()

  await expect(page.getByText('Strengths')).toBeVisible({ timeout: 15000 })
  await expect(page.getByText('Correctness')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Next question' })).toBeVisible()
})