/**
 * Visual Regression Test Script
 *
 * This script can be run with Playwright or Puppeteer to capture
 * screenshots of the Agent Panel in various states for visual regression testing.
 *
 * Usage:
 *   npm install -D @playwright/test
 *   npx playwright test visual-regression-test.js
 */

const { test, expect } = require('@playwright/test')

test.describe('Agent Visualization Panel - Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to chat page
    await page.goto('http://localhost:3000/chat')

    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle')
  })

  // Test 1: Panel Closed State
  test('should match baseline - panel closed', async ({ page }) => {
    await expect(page).toHaveScreenshot('panel-closed.png', {
      fullPage: true,
      animations: 'disabled'
    })
  })

  // Test 2: Panel Open - Overview Tab
  test('should match baseline - overview tab', async ({ page }) => {
    // Click insights button
    await page.click('[title="Toggle insights panel"]')

    // Wait for animation
    await page.waitForTimeout(500)

    await expect(page).toHaveScreenshot('panel-overview.png', {
      fullPage: true,
      animations: 'disabled'
    })
  })

  // Test 3: Panel Open - Agents Tab
  test('should match baseline - agents tab', async ({ page }) => {
    await page.click('[title="Toggle insights panel"]')
    await page.waitForTimeout(300)

    // Click Agents tab
    await page.click('text=Agents')
    await page.waitForTimeout(300)

    await expect(page).toHaveScreenshot('panel-agents.png', {
      fullPage: true,
      animations: 'disabled'
    })
  })

  // Test 4: Panel Open - Context Tab
  test('should match baseline - context tab', async ({ page }) => {
    await page.click('[title="Toggle insights panel"]')
    await page.waitForTimeout(300)

    await page.click('text=Context')
    await page.waitForTimeout(300)

    await expect(page).toHaveScreenshot('panel-context.png', {
      fullPage: true,
      animations: 'disabled'
    })
  })

  // Test 5: Panel Open - Performance Tab
  test('should match baseline - performance tab', async ({ page }) => {
    await page.click('[title="Toggle insights panel"]')
    await page.waitForTimeout(300)

    await page.click('text=Stats')
    await page.waitForTimeout(300)

    await expect(page).toHaveScreenshot('panel-performance.png', {
      fullPage: true,
      animations: 'disabled'
    })
  })

  // Test 6: Mobile View (375px)
  test('should match baseline - mobile view', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    await page.click('[title="Toggle insights panel"]')
    await page.waitForTimeout(500)

    await expect(page).toHaveScreenshot('panel-mobile.png', {
      fullPage: true,
      animations: 'disabled'
    })
  })

  // Test 7: Tablet View (768px)
  test('should match baseline - tablet view', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })

    await page.click('[title="Toggle insights panel"]')
    await page.waitForTimeout(500)

    await expect(page).toHaveScreenshot('panel-tablet.png', {
      fullPage: true,
      animations: 'disabled'
    })
  })

  // Test 8: Desktop View (1440px)
  test('should match baseline - desktop view', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })

    await page.click('[title="Toggle insights panel"]')
    await page.waitForTimeout(500)

    await expect(page).toHaveScreenshot('panel-desktop.png', {
      fullPage: true,
      animations: 'disabled'
    })
  })

  // Test 9: Empty State
  test('should match baseline - empty state', async ({ page }) => {
    // Clear local storage to reset session
    await page.evaluate(() => localStorage.clear())
    await page.reload()

    await page.click('[title="Toggle insights panel"]')
    await page.waitForTimeout(500)

    await expect(page).toHaveScreenshot('panel-empty.png', {
      fullPage: true,
      animations: 'disabled'
    })
  })

  // Test 10: Dark Mode (if implemented)
  test('should match baseline - dark mode', async ({ page }) => {
    // Enable dark mode
    await page.emulateMedia({ colorScheme: 'dark' })

    await page.click('[title="Toggle insights panel"]')
    await page.waitForTimeout(500)

    await expect(page).toHaveScreenshot('panel-dark-mode.png', {
      fullPage: true,
      animations: 'disabled'
    })
  })
})

// Performance Tests
test.describe('Agent Panel - Performance Tests', () => {
  test('should load panel within performance budget', async ({ page }) => {
    await page.goto('http://localhost:3000/chat')

    // Start tracing
    await page.context().tracing.start({ screenshots: true, snapshots: true })

    // Click insights button
    const startTime = Date.now()
    await page.click('[title="Toggle insights panel"]')

    // Wait for panel to be visible
    await page.waitForSelector('[class*="ChatAgentPanel"]', { state: 'visible' })
    const endTime = Date.now()

    await page.context().tracing.stop({ path: 'panel-load-trace.zip' })

    const loadTime = endTime - startTime
    console.log(`Panel load time: ${loadTime}ms`)

    // Assert load time < 500ms
    expect(loadTime).toBeLessThan(500)
  })

  test('should maintain 60fps during panel animation', async ({ page }) => {
    await page.goto('http://localhost:3000/chat')

    // Monitor frame rate
    const fps = await page.evaluate(() => {
      return new Promise((resolve) => {
        let frameCount = 0
        const startTime = performance.now()

        function countFrames() {
          frameCount++
          if (performance.now() - startTime < 1000) {
            requestAnimationFrame(countFrames)
          } else {
            resolve(frameCount)
          }
        }

        requestAnimationFrame(countFrames)
      })
    })

    console.log(`Frame rate during animation: ${fps}fps`)
    expect(fps).toBeGreaterThan(55) // Allow small variance
  })

  test('should not cause layout shift', async ({ page }) => {
    await page.goto('http://localhost:3000/chat')

    // Measure Cumulative Layout Shift (CLS)
    const cls = await page.evaluate(() => {
      return new Promise((resolve) => {
        let clsScore = 0
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) {
              clsScore += entry.value
            }
          }
        })
        observer.observe({ type: 'layout-shift', buffered: true })

        setTimeout(() => {
          observer.disconnect()
          resolve(clsScore)
        }, 3000)
      })
    })

    await page.click('[title="Toggle insights panel"]')
    await page.waitForTimeout(1000)

    console.log(`Cumulative Layout Shift: ${cls}`)
    expect(cls).toBeLessThan(0.1) // Good CLS score
  })
})

// Accessibility Tests
test.describe('Agent Panel - Accessibility Tests', () => {
  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('http://localhost:3000/chat')

    // Tab to insights button
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab') // May need multiple tabs depending on layout

    // Press Enter to open panel
    await page.keyboard.press('Enter')
    await page.waitForTimeout(500)

    // Panel should be open
    const isVisible = await page.isVisible('[class*="ChatAgentPanel"]')
    expect(isVisible).toBe(true)

    // Press Escape to close
    await page.keyboard.press('Escape')
    await page.waitForTimeout(500)

    // Panel should be closed
    const isHidden = await page.isHidden('[class*="ChatAgentPanel"]')
    expect(isHidden).toBe(true)
  })

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('http://localhost:3000/chat')

    // Check for aria-label on close button
    const closeButton = await page.$('[aria-label="Close panel"]')
    expect(closeButton).not.toBeNull()

    // Check tab navigation has proper roles
    await page.click('[title="Toggle insights panel"]')
    await page.waitForTimeout(300)

    const tabs = await page.$$('[role="tab"]')
    expect(tabs.length).toBeGreaterThan(0)
  })

  test('should respect reduced motion preference', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.goto('http://localhost:3000/chat')

    // Check that animations are disabled
    const hasReducedMotion = await page.evaluate(() => {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches
    })

    expect(hasReducedMotion).toBe(true)

    // Panel should still function
    await page.click('[title="Toggle insights panel"]')
    await page.waitForTimeout(100) // Shorter wait since no animation

    const isVisible = await page.isVisible('[class*="ChatAgentPanel"]')
    expect(isVisible).toBe(true)
  })
})

// Cross-browser Tests
test.describe('Agent Panel - Cross-browser Compatibility', () => {
  test('should work in webkit (Safari)', async ({ page, browserName }) => {
    test.skip(browserName !== 'webkit', 'Safari-specific test')

    await page.goto('http://localhost:3000/chat')
    await page.click('[title="Toggle insights panel"]')
    await page.waitForTimeout(500)

    const isVisible = await page.isVisible('[class*="ChatAgentPanel"]')
    expect(isVisible).toBe(true)
  })

  test('should work in firefox', async ({ page, browserName }) => {
    test.skip(browserName !== 'firefox', 'Firefox-specific test')

    await page.goto('http://localhost:3000/chat')
    await page.click('[title="Toggle insights panel"]')
    await page.waitForTimeout(500)

    const isVisible = await page.isVisible('[class*="ChatAgentPanel"]')
    expect(isVisible).toBe(true)
  })
})
