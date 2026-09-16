// Document/publication checks only. Not a compiler or agent-evaluation oracle.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, lstatSync, readFileSync, realpathSync } from 'node:fs';
import { dirname, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const allowed = new Set([
  '.gitignore',
  'README.md',
  'AGENTS.md',
  '.github/CODEOWNERS',
  '.github/pull_request_template.md',
  '.github/workflows/quality.yml',
  'program.md',
  '.agents/skills/run-bounded-change-loop/SKILL.md',
  '.agents/skills/review-to-verified-pr/SKILL.md',
  'scripts/trial.py',
  'tests/test_trial.py',
  'examples/group-reduction/candidate.py',
  'examples/group-reduction/check.py',
  'examples/furiosa-double-buffering/tests/double_buffering_tests.rs',
  'examples/furiosa-double-buffering/tests/support/double_buffering_reference.rs',
  'examples/furiosa-double-buffering/controls/reuse-first-trf.patch',
  'examples/furiosa-mapping-parser/tests.patch',
  'examples/furiosa-mapping-parser/controls/accept-bracket-extent.patch',
  'docs/quality.md',
  'docs/merge.md',
  'docs/kernels/double-buffering.md',
  'scripts/check.mjs',
  'pyproject.toml',
  'requirements-dev.txt',
  'package.json',
  'package-lock.json',
  'biome.json',
]);
const sensitive =
  /(?:\/Users\/|\/home\/)[\w.-]+\/|file:\/\/|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{24,}|-----BEGIN [A-Z ]*PRIVATE KEY-----/;

// This repository uses inline/reference links and ATX headings. Ignore fenced
// examples when discovering links/headings, but still scan all bytes for secrets.
function markdownBody(text) {
  let fence = null;
  return text
    .split('\n')
    .filter((line) => {
      const marker = /^\s{0,3}(`{3,}|~{3,})/.exec(line);
      if (marker && !fence) {
        fence = marker[1];
        return false;
      }
      if (marker && fence && marker[1][0] === fence[0] && marker[1].length >= fence.length) {
        fence = null;
        return false;
      }
      return !fence;
    })
    .join('\n');
}
function links(text) {
  return [...markdownBody(text).matchAll(/\]\(([^)]+)\)|href=["']([^"']+)["']|^\[[^\]]+\]:\s*(\S+)/gm)].map((match) =>
    (match[1] || match[2] || match[3]).replace(/^<(.+)>$/, '$1'),
  );
}
function anchors(text) {
  const body = markdownBody(text);
  const ids = new Set([...body.matchAll(/\bid=["']([^"']+)["']/g)].map((match) => match[1]));
  for (const match of body.matchAll(/^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$/gm)) {
    const base = match[1]
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/<[^>]+>/g, '')
      .toLowerCase()
      .replace(/[^\p{L}\p{N}\p{M}_\-\s]/gu, '')
      .replace(/\s/g, '-');
    let id = base,
      suffix = 0;
    while (ids.has(id)) id = `${base}-${++suffix}`;
    ids.add(id);
  }
  return ids;
}
function publicTarget(file, href) {
  const [pathname, fragment] = href.split('#');
  const target = pathname ? resolve(dirname(resolve(root, file)), decodeURIComponent(pathname)) : resolve(root, file);
  const name = relative(root, target);
  assert.ok(
    allowed.has(name) || [...allowed].some((page) => page.startsWith(`${name}/`)),
    `Link outside public files: ${file} -> ${href}`,
  );
  return { target, name, fragment: fragment === undefined ? null : decodeURIComponent(fragment) };
}
function requireAnchor(text, anchor) {
  assert.ok(anchors(text).has(anchor), `Missing Markdown anchor: ${anchor}`);
}
// Keep entrypoint routes complete; content/code agreement still needs review.
function checkIndexLinks(index, pages) {
  const targets = new Set(links(index).map((href) => href.split('#')[0]));
  for (const page of pages) assert.ok(targets.has(page), `Page missing from index: ${page}`);
}

// Docs-only work still runs the public/CI contract check. Unknown paths or
// shared policy changes select every language rather than silently omitting one.
function ciPlan(paths) {
  const plan = { python: false, javascript: false, rust: false };
  for (const path of paths) {
    if (/\.py$/.test(path)) plan.python = true;
    else if (/\.mjs$|^(package(?:-lock)?|biome)\.json$/.test(path)) plan.javascript = true;
    else if (/\.(rs|patch)$/.test(path)) plan.rust = true;
    else if (path === 'README.md' || path === 'docs/merge.md' || path === '.github/pull_request_template.md') continue;
    else return { python: true, javascript: true, rust: true };
    if (path === 'scripts/check.mjs') return { python: true, javascript: true, rust: true };
  }
  return plan;
}

function requireResults(plan, results) {
  assert.equal(results.system, 'success', 'Public/CI contract job did not succeed');
  for (const language of ['python', 'javascript', 'rust']) {
    assert.ok(plan[language] === 'true' || plan[language] === 'false', `Missing plan: ${language}`);
    assert.equal(
      results[language],
      plan[language] === 'true' ? 'success' : 'skipped',
      `Unexpected CI result: ${language}`,
    );
  }
}

assert.ok(sensitive.test(`/${['Users', 'example', 'private'].join('/')}`), 'Path check self-test');
assert.ok(sensitive.test(`sk-${'x'.repeat(24)}`), 'Secret check self-test');
assert.ok(!allowed.has('.local/private.md'), 'Private scope self-test');
checkIndexLinks('[Page](01.md#entry)', ['01.md']);
assert.throws(() => checkIndexLinks('[Page](01.md)', ['02.md']), /missing from index/);
assert.equal(publicTarget('AGENTS.md', 'docs/quality.md#mapping-parser').name, 'docs/quality.md');
assert.throws(() => publicTarget('AGENTS.md', '.local/private.md'), /outside public/);
assert.throws(() => publicTarget('AGENTS.md', '../outside.md'), /outside public/);
const anchorSample = '## 3. 코드와 `State`\n## Same\n## Same\n```md\n# Hidden\n```\n';
assert.deepEqual([...anchors(anchorSample)], ['3-코드와-state', 'same', 'same-1']);
requireAnchor(anchorSample, 'same-1');
assert.throws(() => requireAnchor(anchorSample, 'hidden'), /Missing Markdown anchor/);
assert.throws(() => requireAnchor(anchorSample, 'absent'), /Missing Markdown anchor/);
assert.deepEqual(ciPlan(['README.md']), { python: false, javascript: false, rust: false });
assert.deepEqual(ciPlan(['scripts/trial.py', 'examples/check.rs']), { python: true, javascript: false, rust: true });
assert.deepEqual(ciPlan(['package-lock.json']), { python: false, javascript: true, rust: false });
for (const path of [
  'AGENTS.md',
  'program.md',
  'pyproject.toml',
  'scripts/check.mjs',
  '.github/workflows/quality.yml',
  'new.lang',
]) {
  assert.deepEqual(ciPlan([path]), { python: true, javascript: true, rust: true });
}
const testPlan = { python: 'true', javascript: 'false', rust: 'false' };
const testResults = { system: 'success', python: 'success', javascript: 'skipped', rust: 'skipped' };
requireResults(testPlan, testResults);
for (const result of ['skipped', 'cancelled', 'failure', '', undefined]) {
  assert.throws(() => requireResults(testPlan, { ...testResults, python: result }), /Unexpected CI result/);
  assert.throws(() => requireResults(testPlan, { ...testResults, system: result }), /did not succeed/);
}
assert.throws(() => requireResults({}, testResults), /Missing plan/);
assert.throws(() => requireResults(testPlan, { ...testResults, javascript: 'success' }), /Unexpected CI result/);
const mode = process.argv[2];
assert.ok(
  process.argv.length === 2 ||
    (process.argv.length === 3 && ['--self-test', '--ci-gate'].includes(mode)) ||
    (process.argv.length === 4 && mode === '--ci-plan'),
  'Usage: check.mjs [--self-test | --ci-plan BASE_SHA | --ci-gate]',
);
if (mode === '--ci-plan') {
  const base = process.argv[3];
  let plan = { python: true, javascript: true, rust: true };
  // An initial push or unavailable base must run all jobs. --no-renames emits
  // both old and new paths, covering extension-changing renames and deletions.
  if (/^[a-f0-9]{40}$/.test(base) && !/^0+$/.test(base)) {
    try {
      const paths = execFileSync('git', ['diff', '--name-only', '--no-renames', '-z', base, 'HEAD'], { cwd: root })
        .toString()
        .split('\0')
        .filter(Boolean);
      plan = ciPlan(paths);
    } catch {
      console.error('Diff base unavailable: running all language checks');
    }
  }
  for (const [language, required] of Object.entries(plan)) console.log(`${language}=${required}`);
  process.exit(0);
}
if (mode === '--ci-gate') {
  requireResults(JSON.parse(process.env.CI_PLAN || '{}'), JSON.parse(process.env.CI_RESULTS || '{}'));
  console.log('PASS: all selected jobs succeeded; only unselected language jobs were skipped');
  process.exit(0);
}
if (process.argv[2] === '--self-test') {
  console.log(
    JSON.stringify({
      status: 'PASS',
      scope: 'public-path, secret, link, anchor and CI selection/gate regressions; no repository scan',
    }),
  );
  process.exit(0);
}

const files = execFileSync('git', ['ls-files', '--cached', '--others', '--exclude-standard', '-z'], { cwd: root })
  .toString()
  .split('\0')
  .filter(Boolean);
assert.deepEqual([...new Set(files)].sort(), [...allowed].sort(), 'Missing or unexpected public file');
const texts = new Map();
for (const file of files) {
  const full = resolve(root, file);
  assert.ok(existsSync(full), `Missing public file: ${file}`);
  assert.ok(lstatSync(full).isFile() && !lstatSync(full).isSymbolicLink(), `Not a regular public file: ${file}`);
  assert.equal(realpathSync(full), full, `Symlink ancestor in public file: ${file}`);
  const text = readFileSync(full, 'utf8');
  texts.set(file, text);
  assert.ok(!sensitive.test(text), `Sensitive-looking text: ${file}`);
  assert.ok(!text.includes('\r'), `Non-LF line endings: ${file}`);
}
for (const [file, text] of texts) {
  if (!file.endsWith('.md')) continue;
  assert.ok(!text.includes('[['), `Unresolved wiki link: ${file}`);
  for (const href of links(text)) {
    if (/^(https?:|mailto:)/.test(href)) continue;
    const { target, name, fragment } = publicTarget(file, href);
    assert.ok(existsSync(target), `Broken link: ${file} -> ${href}`);
    assert.equal(realpathSync(target), target, `Symlink link target: ${file} -> ${href}`);
    if (fragment !== null) {
      assert.ok(name.endsWith('.md') && texts.has(name), `Anchor target is not Markdown: ${file} -> ${href}`);
      requireAnchor(texts.get(name), fragment);
    }
  }
}
const agents = readFileSync(resolve(root, 'AGENTS.md'), 'utf8');
const skillPages = files.filter((file) => file.startsWith('.agents/skills/') && file.endsWith('/SKILL.md'));
checkIndexLinks(agents, [
  ...skillPages,
  'program.md',
  'docs/quality.md',
  'docs/merge.md',
  'docs/kernels/double-buffering.md',
]);
checkIndexLinks(readFileSync(resolve(root, '.agents/skills/run-bounded-change-loop/SKILL.md'), 'utf8'), [
  '../../../program.md',
]);
checkIndexLinks(readFileSync(resolve(root, '.agents/skills/review-to-verified-pr/SKILL.md'), 'utf8'), [
  '../../../docs/quality.md',
  '../../../docs/merge.md',
  '../../../docs/kernels/double-buffering.md',
]);
const pr = readFileSync(resolve(root, '.github/pull_request_template.md'), 'utf8');
for (const field of [
  'Baseline SHA',
  'PR head SHA',
  'PR base SHA',
  'checkout SHA',
  'NOT_RUN',
  'post-merge',
  'Human review',
  'Review requirement',
  'Environment evidence',
  'State after failure',
  'expected rejection from tool failure',
])
  assert.ok(pr.includes(field), field);
const workflow = readFileSync(resolve(root, '.github/workflows/quality.yml'), 'utf8');
for (const fragment of [
  'always()',
  'needs: [lab-system, lab-python, lab-javascript, lab-rust]',
  'contents: read',
  'persist-credentials: false',
  'branches: [dev, main]',
  'node scripts/check.mjs',
  'unittest.defaultTestLoader.discover',
  '--ci-plan',
  '--ci-gate',
  'python -m ruff check',
  'python -m ruff format --check',
  'python -m mypy',
  'npm ci --ignore-scripts',
  'npm run check',
  'clippy-driver',
  'git apply --check',
  'actionlint@v1.7.12',
])
  assert.ok(workflow.includes(fragment), fragment);
assert.ok(!workflow.includes('pull_request_target'), 'Do not run PR code with a privileged event');
assert.ok(!workflow.includes('continue-on-error'), 'Required quality failures cannot be ignored');
console.log(
  JSON.stringify({
    status: 'PASS',
    publicFiles: files.length,
    skillRoutes: skillPages.length,
    scope: 'public files, Markdown links/anchors and workflow contracts; no Rust/cloud run',
  }),
);
