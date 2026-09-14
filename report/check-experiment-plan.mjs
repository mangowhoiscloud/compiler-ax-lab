// Arithmetic only: deterministic queue examples, not compiler or cloud measurements.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

export function schedule(k, pL, pE, { g = 10, e = 20, s = 15, f = 15, barrier = false } = {}) {
  for (const n of [k, pL, pE]) assert.ok(Number.isSafeInteger(n) && n > 0);
  for (const n of [g, e]) assert.ok(Number.isFinite(n) && n > 0);
  for (const n of [s, f]) assert.ok(Number.isFinite(n) && n >= 0);
  // Uniform generation times and fixed candidate order. No adaptive search or optimality claim.
  const release = Array.from({ length: k }, (_, i) => s + (Math.floor(i / pL) + 1) * g);
  const slots = Array(Math.min(k, pE)).fill(s);
  const trace = release.map((ready, i) => {
    const slot = slots.indexOf(Math.min(...slots));
    const start = Math.max(barrier ? Math.max(...release) : ready, slots[slot]);
    slots[slot] = start + e;
    return { candidate: i + 1, slot, ready, start, end: slots[slot] };
  });
  return { minutes: Math.max(...slots) + f, trace };
}

const cases = [
  [1, 1, 120, 100], [3, 1, 100, 100], [1, 2, 100, 80],
  [3, 2, 80, 80], [1, 3, 80, 80], [3, 3, 60, 60],
];
const html = readFileSync(new URL('./assets/compiler-ax-experiment-approval.html', import.meta.url), 'utf8');
for (const [pL, pE, barrier, ready] of cases) {
  assert.equal(schedule(3, pL, pE, { barrier: true }).minutes, barrier);
  assert.equal(schedule(3, pL, pE).minutes, ready);
  assert.ok(html.includes(`data-timing="${pL},${pE},${barrier},${ready}"`), 'Displayed timing row drift');
}
let checks = 0;
for (let k = 1; k <= 8; k++) for (let g = 1; g <= 8; g++) for (let e = 1; e <= 8; e++) {
  // Independent closed form for a single generation lane and a single execution lane.
  assert.equal(schedule(k, 1, 1, { g, e }).minutes, 30 + g + e + (k - 1) * Math.max(g, e));
  checks++;
}
assert.equal(schedule(1, 1, 1).minutes, 60);
assert.equal(schedule(3, 1, 1, { g: 1, s: 0, f: 0, barrier: true }).minutes - 3, 60);
assert.equal(schedule(3, 3, 2, { e: 32 }).minutes, 104); // Slower per-job execution erases the gain.
assert.ok(2 * 32 > 3 * 20); // Pure CPU replay: 64 minutes is worse than 60.
assert.equal(schedule(3, 8, 8).minutes, 60);
assert.throws(() => schedule(3, 0, 2));
assert.throws(() => schedule(3, 1, 2, { e: NaN }));
assert.throws(() => schedule(3, 1.5, 2));
assert.throws(() => schedule(3, 1, 2, { s: -1 }));
console.log(JSON.stringify({ status: 'PASS', closedFormChecks: checks, timingRows: cases.length,
  readyBaseline: 100, selectedIdeal: 80, selectedWithFiveMinuteOverhead: 85,
  speedup: 100 / 85, scope: 'illustrative arithmetic; no cloud/compiler execution' }));
