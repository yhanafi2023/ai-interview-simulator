# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: interview.spec.ts >> a user can answer a question and receive feedback
- Location: e2e/interview.spec.ts:3:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('button', { name: 'Next question' })
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByRole('button', { name: 'Next question' })

```

```yaml
- banner:
  - navigation:
    - text: InterviewAI
    - link "Home":
      - /url: /
    - link "Dashboard":
      - /url: /dashboard
    - text: Jack
    - button "Log out"
- main:
  - text: Question 1 of 1 behavioral easy
  - paragraph: Tell me about a time you disagreed with a teammate. How did you resolve it?
  - text: Your answer
  - textbox "Your answer" [disabled]:
    - /placeholder: Explain your approach first, then walk through the solution…
    - text: I disagreed with a teammate about whether to add a caching layer before we had measured the actual latency. I asked to spend an afternoon instrumenting the endpoint first. The data showed the bottleneck was a missing database index, not repeated computation, so we fixed the index and skipped the cache entirely. I learned to argue with numbers rather than opinions, and my teammate and I agreed on the outcome quickly once we had them.
  - text: 436 characters Correctness 8/10
  - paragraph: The core approach is sound but skips a key constraint.
  - text: Communication 9/10
  - paragraph: Clear structure. State your assumptions earlier.
  - text: Depth 7/10
  - paragraph: Time complexity is mentioned but not derived.
  - text: Edge cases 6/10
  - paragraph: Empty and single-element inputs are not addressed.
  - heading "Strengths" [level=3]
  - list:
    - listitem: • You explained your approach before writing code.
    - listitem: • Variable naming was clear and consistent.
  - heading "Improvements" [level=3]
  - list:
    - listitem: • Walk through at least one edge case out loud.
    - listitem: • Give the time and space complexity explicitly.
  - heading "Follow-up question" [level=3]
  - paragraph: How would your solution change if the input did not fit in memory?
  - button "Finish session"
- button "Open Tanstack query devtools":
  - img
```

# Test source

```ts
  1  | import { expect, test } from '@playwright/test'
  2  | 
  3  | test('a user can answer a question and receive feedback', async ({ page }) => {
  4  |   await page.goto('/login')
  5  |   await page.getByLabel('Email').fill('jack@example.com')
  6  |   await page.getByLabel('Password').fill('password123')
  7  |   await page.getByRole('button', { name: 'Log in' }).click()
  8  |   await expect(page).toHaveURL(/\/dashboard/)
  9  | 
  10 |   await page.getByLabel('Type').selectOption('behavioral')
  11 |   await page.getByRole('button', { name: 'Start interview' }).click()
  12 | 
  13 |   await expect(page).toHaveURL(/\/interview\//)
  14 | 
  15 |   await page
  16 |     .getByLabel('Your answer')
  17 |     .fill(
  18 |       'I disagreed with a teammate about whether to add a caching layer before we had measured ' +
  19 |         'the actual latency. I asked to spend an afternoon instrumenting the endpoint first. ' +
  20 |         'The data showed the bottleneck was a missing database index, not repeated computation, ' +
  21 |         'so we fixed the index and skipped the cache entirely. I learned to argue with numbers ' +
  22 |         'rather than opinions, and my teammate and I agreed on the outcome quickly once we had them.',
  23 |     )
  24 | 
  25 |   await page.getByRole('button', { name: 'Submit answer' }).click()
  26 | 
  27 |   await expect(page.getByText('Strengths')).toBeVisible({ timeout: 15000 })
  28 |   await expect(page.getByText('Correctness')).toBeVisible()
> 29 |   await expect(page.getByRole('button', { name: 'Next question' })).toBeVisible()
     |                                                                     ^ Error: expect(locator).toBeVisible() failed
  30 | })
```