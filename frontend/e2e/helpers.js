/**
 * Shared E2E test helpers.
 *
 * The codebase has pre-existing template errors in lazy-loaded views
 * that cause Vite's error overlay, and an onboarding tour that blocks
 * page interaction. These helpers handle both.
 */

/** Suppress Vite error overlay by defining a no-op custom element before Vite's client runs. */
export async function suppressViteOverlay(page) {
  await page.addInitScript(() => {
    if (!customElements.get('vite-error-overlay')) {
      customElements.define(
        'vite-error-overlay',
        class extends HTMLElement {
          connectedCallback() {
            this.style.display = 'none'
          }
        },
      )
    }
  })
}

/** Dismiss the onboarding tour if it appears. */
export async function dismissTour(page) {
  const skipBtn = page.getByRole('button', { name: 'Skip tour' })
  if (await skipBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await skipBtn.first().click()
    // Wait for tour to fully close
    await skipBtn.first().waitFor({ state: 'hidden', timeout: 2000 }).catch(() => {})
  }
}

/** Standard page setup: suppress overlay, navigate, dismiss tour. */
export async function setupPage(page, url = '/') {
  await suppressViteOverlay(page)
  await page.goto(url)
  await dismissTour(page)
}
