import { expect, test } from '@playwright/test'

test('redirects an unauthenticated user away from the dashboard', async ({ page }) => {
  await page.goto('/dashboard')
  await expect(page).toHaveURL(/\/login/)
})

test('a user can log in and reach the dashboard', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Email').fill('jack@example.com')
  await page.getByLabel('Password').fill('password123')
  await page.getByRole('button', { name: 'Log in' }).click()

  await expect(page).toHaveURL(/\/dashboard/)
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
})

test('shows the server error for a wrong password', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Email').fill('jack@example.com')
  await page.getByLabel('Password').fill('wrongpassword')
  await page.getByRole('button', { name: 'Log in' }).click()

  await expect(page.getByText('Invalid email or password')).toBeVisible()
})

test('rejects an invalid email before sending a request', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Email').fill('notanemail')
  await page.getByLabel('Password').fill('password123')
  await page.getByRole('button', { name: 'Log in' }).click()

  await expect(page.getByText('Enter a valid email address')).toBeVisible()
})