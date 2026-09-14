// Document/publication checks only. Not a compiler or agent-evaluation oracle.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import '../report/check-experiment-plan.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const allowed = new Set([
  '.gitignore', 'README.md', 'AGENTS.md', '.github/CODEOWNERS',
  '.github/pull_request_template.md', '.github/workflows/quality.yml',
  'program.md', '.agents/skills/run-bounded-change-loop/SKILL.md', 'references/source-layouts.md',
  'references/frontier-engineering-2026.md',
  '.agents/skills/review-to-verified-pr/SKILL.md',
  '.agents/skills/review-to-verified-pr/references/review-evidence.md',
  'scripts/trial.py', 'tests/test_trial.py',
  'examples/group-reduction/candidate.py', 'examples/group-reduction/check.py',
  'examples/furiosa-double-buffering/tests/double_buffering_tests.rs',
  'examples/furiosa-double-buffering/tests/support/double_buffering_reference.rs',
  'examples/furiosa-double-buffering/controls/reuse-first-trf.patch',
  'docs/context.md', 'docs/experiment.md', 'docs/quality.md', 'docs/merge.md', 'docs/sources.md',
  'docs/architecture/00-OVERVIEW.md', 'docs/architecture/01-LOCAL-TRIAL.md',
  'docs/architecture/02-REMOTE-EXECUTION.md',
  'docs/kernels/double-buffering.md',
  'docs/token-factory-sandbox.md',
  'scripts/check.mjs', 'report/check-experiment-plan.mjs', 'report/render-experiment-approval.mjs',
  'report/assets/compiler-ax-experiment-approval.html',
  ...[1, 2, 3].map(i => `report/assets/compiler-ax-experiment-approval-${i}.png`),
]);
const files = execFileSync('git', ['ls-files', '--cached', '--others', '--exclude-standard', '-z'], { cwd: root })
  .toString().split('\0').filter(Boolean);
assert.equal(new Set(files).size, allowed.size, 'Missing or unexpected public file');
const sensitive = /(?:\/Users\/|\/home\/)[\w.-]+\/|file:\/\/|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{24,}|-----BEGIN [A-Z ]*PRIVATE KEY-----/;
assert.ok(sensitive.test('/' + ['Users', 'example', 'private'].join('/')), 'Path check self-test');
assert.ok(!allowed.has('.local/private.md'), 'Private scope self-test');
for (const file of files) {
  assert.ok(allowed.has(file), `Not in public allowlist: ${file}`);
  const bytes = readFileSync(resolve(root, file));
  if (file.endsWith('.png')) {
    assert.equal(bytes.subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
    continue; // Rendered figures need separate visual review.
  }
  const text = bytes.toString('utf8');
  assert.ok(!sensitive.test(text), `Sensitive-looking text: ${file}`);
  assert.ok(!text.includes('\r'), `Non-LF line endings: ${file}`);
  if (!/\.(md|html)$/.test(file)) continue;
  assert.ok(!text.includes('[['), `Unresolved wiki link: ${file}`);
  const links = [...text.matchAll(/\]\(([^)]+)\)|href="([^"]+)"/g)];
  for (const match of links) {
    const href = match[1] || match[2];
    if (/^(https?:|mailto:|#)/.test(href)) continue;
    const target = resolve(dirname(resolve(root, file)), decodeURIComponent(href.split('#')[0]));
    assert.ok(target.startsWith(root) && existsSync(target), `Broken or escaping link: ${file} -> ${href}`);
  }
}
// Keep entrypoint routes complete; content/code agreement still needs review.
function checkIndexLinks(index, pages) {
  const links = new Set([...index.matchAll(/\]\(([^)#]+)(?:#[^)]*)?\)/g)].map(match => match[1]));
  for (const page of pages) assert.ok(links.has(page), `Page missing from index: ${page}`);
}
checkIndexLinks('[Page](01.md#entry)', ['01.md']);
assert.throws(() => checkIndexLinks('[Page](01.md)', ['02.md']), /missing from index/);
const architecture = files.filter(file => file.startsWith('docs/architecture/') && file.endsWith('.md'));
const indexPath = 'docs/architecture/00-OVERVIEW.md';
checkIndexLinks(readFileSync(resolve(root, indexPath), 'utf8'),
  architecture.filter(file => file !== indexPath).map(file => file.slice('docs/architecture/'.length)));
const agents = readFileSync(resolve(root, 'AGENTS.md'), 'utf8');
assert.ok(agents.includes(`](${indexPath})`), 'AGENTS must route to the architecture index');
for (const section of ['## 3. 코드와 커밋의 컨벤션', '## 4. 공개 리뷰를 실행 가능한 요구로 바꾼다',
  '## 5. 변경을 검사하고 인계한다']) assert.ok(agents.includes(section), `Missing agent convention section: ${section}`);
checkIndexLinks(agents, files.filter(file => file.startsWith('.agents/skills/') && file.endsWith('/SKILL.md')));
const kernels = files.filter(file => file.startsWith('docs/kernels/') && file.endsWith('.md'));
checkIndexLinks(agents, kernels);
checkIndexLinks(readFileSync(resolve(root, indexPath), 'utf8'), kernels.map(file => file.replace('docs/', '../')));
checkIndexLinks(readFileSync(resolve(root, '.agents/skills/review-to-verified-pr/SKILL.md'), 'utf8'),
  kernels.map(file => `../../../${file}`));
const html = readFileSync(resolve(root, 'report/assets/compiler-ax-experiment-approval.html'), 'utf8');
assert.deepEqual([...html.matchAll(/data-quality="([a-z-]+)"/g)].map(m => m[1]),
  ['contract-environment', 'scope-code-quality', 'output-behavior', 'integration-docs', 'independent-final', 'human-adoption']);
for (const anchor of [...html.matchAll(/href="#([^"]+)"/g)].map(m => m[1])) assert.ok(html.includes(`id="${anchor}"`));
const pr = readFileSync(resolve(root, '.github/pull_request_template.md'), 'utf8');
for (const field of ['Baseline SHA', 'PR head SHA', 'PR base SHA', 'checkout SHA', 'NOT_RUN', 'post-merge', '사람 검토',
  '관련 리뷰 요구', '환경 확인 근거', '실패 후 남은 상태', '기대 거절과 도구 실패']) assert.ok(pr.includes(field), field);
const workflow = readFileSync(resolve(root, '.github/workflows/quality.yml'), 'utf8');
for (const fragment of ['always()', 'needs: [lab-docs]', 'contents: read', 'node scripts/check.mjs', 'test "$DOCS_RESULT" = success']) assert.ok(workflow.includes(fragment), fragment);
assert.ok(!workflow.includes('pull_request_target'), 'Do not run PR code with a privileged event');
console.log(JSON.stringify({ status: 'PASS', publicFiles: files.length, architecturePages: architecture.length, qualityStages: 6, scope: 'local docs, public paths and illustrative arithmetic; no Rust/cloud run' }));
