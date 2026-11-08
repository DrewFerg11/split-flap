// Execute the actual Bash mapping in both workflows, so deploy/cleanup cannot drift.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

function mapping(file) {
  const yaml = readFileSync(new URL('../../.github/workflows/' + file, import.meta.url), 'utf8');
  const body = yaml.match(/# BEGIN preview key\r?\n([\s\S]+?)\s*# END preview key/)?.[1];
  assert(body, file + ': preview key block missing');
  return body.split(/\r?\n/).map((line) => line.trim()).join('\n').trim();
}

const deploy = mapping('docs-deploy.yml');
const cleanup = mapping('docs-cleanup.yml');
assert.equal(deploy, cleanup, 'Deploy and cleanup must use identical preview keys');
const branches = [
  'feat/a-b', 'feat/a/b', 'docs/start', 'feature/demo', 'feat/a.b', 'feat/a_b',
  'feat/café', 'feat/caf-', 'feat/' + 'a'.repeat(120), 'feat/' + 'a'.repeat(120) + 'b',
];
const paths = new Set();
for (const branch of branches) {
  const key = execFileSync('bash', ['-e', '-o', 'pipefail', '-c', deploy + '\nprintf "%s" "$SAFE_BRANCH"'], {
    env: { ...process.env, BRANCH: branch }, encoding: 'utf8',
  });
  const hash = createHash('sha256').update(branch).digest('hex').slice(0, 16);
  assert(key.endsWith('-' + hash), 'Must hash the original branch bytes');
  assert.match(key, /^(docs|feat|feature)-[a-zA-Z0-9._-]+-[a-f0-9]{16}$/);
  assert(key.length <= 97, 'Readable prefix must be bounded for filesystem limits');
  assert(!paths.has(key), 'Distinct branches collided: ' + branch);
  paths.add(key);
}
console.log('Verified identical deploy/cleanup mapping and ' + branches.length + ' distinct preview keys.');
