import { expect, test } from '@playwright/test'

test('persona to graph to review flow', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('Recurring people, without identity lookup.')).toBeVisible()
  await page.getByText('P001').first().click()
  await expect(page.getByText('OPEN GRAPH →')).toBeVisible()
  await page.getByText('OPEN GRAPH →').click()
  await expect(page.getByText(/Network around/)).toBeVisible()
  await page.getByRole('button', { name: 'REVIEW' }).click()
  await expect(page.getByText('Abstention is a feature.')).toBeVisible()
  await page.getByRole('button', { name: 'LEAVE UNKNOWN' }).first().click()
})
