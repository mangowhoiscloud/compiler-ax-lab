// Optional render check: reuse an installed Playwright and browser; no downloads.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import './check-experiment-plan.mjs';
assert.ok(process.env.PLAYWRIGHT_PACKAGE && process.env.CHROMIUM_EXECUTABLE,
  'Set PLAYWRIGHT_PACKAGE (absolute package.json) and CHROMIUM_EXECUTABLE');
const require = createRequire(process.env.PLAYWRIGHT_PACKAGE);
const { chromium } = require('./');
const source = new URL('./assets/compiler-ax-experiment-approval.html', import.meta.url);
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_EXECUTABLE, headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1400, height: 1000 }, deviceScaleFactor: 2 });
  await page.goto(source.href, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const timings = await page.locator('[data-timing]').evaluateAll(rows => rows.map(row => {
    const expected = row.dataset.timing.split(',').map(Number);
    const cells = [...row.cells].map(c => c.textContent);
    return { expected, actual: [...cells[0].matchAll(/\d+/g)].map(m => Number(m[0])).concat(cells.slice(1).map(c => parseInt(c, 10))) };
  }));
  for (const row of timings) assert.deepEqual(row.actual, row.expected, 'Visible timing text drift');
  const missingAnchors = await page.locator('a[href^="#"]').evaluateAll(links => links.filter(a => !document.getElementById(a.hash.slice(1))).map(a => a.hash));
  assert.deepEqual(missingAnchors, [], 'Broken local anchor');
  assert.deepEqual(await page.locator('[data-quality]').evaluateAll(rows => rows.map(row => row.dataset.quality)),
    ['contract-environment', 'scope-code-quality', 'output-behavior', 'integration-docs', 'independent-final', 'human-adoption'],
    'Quality contract rows missing or reordered');
  const figures = page.locator('.sheet > svg');
  assert.equal(await figures.count(), 3);
  for (let i = 0; i < 3; i++) {
    const figure = figures.nth(i);
    const qa = await figure.evaluate(svg => {
      const labels = [...svg.querySelectorAll('text')].map(t => {
        const b = t.getBBox();
        return { text: t.textContent, x: b.x, y: b.y, w: b.width, h: b.height };
      });
      const outside = labels.filter(b => b.x < 0 || b.y < 0 || b.x + b.w > 1400 || b.y + b.h > 900);
      const overlaps = [];
      for (let a = 0; a < labels.length; a++) for (let b = a + 1; b < labels.length; b++) {
        const x = labels[a], y = labels[b];
        if (x.x < y.x + y.w && x.x + x.w > y.x && x.y < y.y + y.h && x.y + x.h > y.y) overlaps.push([x.text, y.text]);
      }
      return { title: svg.querySelector('title').textContent, labels: labels.length, outside, overlaps };
    });
    console.log(JSON.stringify(qa));
    assert.deepEqual(qa.outside, [], `Figure ${i + 1}: out-of-canvas text`);
    assert.deepEqual(qa.overlaps, [], `Figure ${i + 1}: overlapping labels`);
    const target = fileURLToPath(new URL(`./assets/compiler-ax-experiment-approval-${i + 1}.png`, import.meta.url));
    await figure.screenshot({ path: target });
    console.log(target);
  }
  assert.equal(await page.locator('body').evaluate(b => b.scrollWidth > innerWidth), false, 'Horizontal overflow');
} finally {
  await browser.close();
}
