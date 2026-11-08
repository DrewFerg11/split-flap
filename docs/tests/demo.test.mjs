import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createDrum, forwardPath, prepareFrame, validateLayout } from '../public/demo/engine/drums.js';
import { MotionController } from '../public/demo/engine/motion.js';
import { app } from '../public/demo/premier-league/config.js';
import { loadDrums } from '../public/demo/premier-league/flaps.js';
import { wildcards } from '../public/demo/premier-league/config.js';

const flapSets = JSON.parse(readFileSync(new URL('../../applications/premier-league/flap-sets/flap-sets.json', import.meta.url), 'utf8'));

test('all application flap entries reach the demo at their firmware indices', () => {
  const keys = { name: 'name', digit: 'digit', header_name: 'hname', header_digit: 'hdigit' };
  const kinds = new Set();
  assert.equal(Object.keys(app.drums).length, 4);
  for (const [key, id] of Object.entries(keys)) {
    assert.equal(app.drums[id].flaps.length, flapSets.flaps);
    let wildcard = 0;
    for (const [index, entry] of flapSets.drums[key].entries()) {
      kinds.add(entry.kind);
      let expected;
      switch (entry.kind) {
        case 'blank': expected = ''; break;
        case 'open': expected = '@open'; break;
        case 'divider': expected = '|divider'; break;
        case 'text': expected = entry.text; break;
        case 'colour': expected = 'c:' + entry.colour; break;
        case 'symbol': expected = '#' + (entry.symbol === 'wildcard' ? wildcards[key][wildcard++]
          : entry.symbol === 'pl-lion' ? 'lion' : entry.symbol); break;
        default: assert.fail('Uncovered JSON kind: ' + entry.kind);
      }
      assert.equal(app.drums[id].flaps[index], expected, key + ' flap ' + index);
    }
  }
  assert.deepEqual([...kinds].sort(), ['blank', 'colour', 'divider', 'open', 'symbol', 'text']);
});

test('application edits flow through the adapter and unsupported definitions fail clearly', () => {
  const source = structuredClone(flapSets);
  const options = { colours: app.colours, icons: app.icons, wildcards };
  source.drums.name[1] = { kind: 'text', text: 'UPDATED CLUB' };
  assert.equal(loadDrums(source, options).name.flaps[1], 'UPDATED CLUB');
  source.drums.name[1] = { kind: 'future-kind' };
  assert.throws(() => loadDrums(source, options), /Unsupported flap in name/);
  assert.throws(() => loadDrums(flapSets, { ...options, wildcards: {} }), /Unsupported flap in digit/);
  source.drums.name.pop();
  assert.throws(() => loadDrums(source, options), /Invalid drum: name/);
});

test('forward paths wrap, stay put, use the nearest duplicate, and never target a spare', () => {
  const drum = createDrum('short', { flaps: ['', 'A', 'B', 'A', '@open'] });
  assert.deepEqual(forwardPath(drum, 4, 'A'), [0, 1]);
  assert.deepEqual(forwardPath(drum, 2, 'A'), [3]);
  assert.deepEqual(forwardPath(drum, 3, 'A'), []);
  assert.equal(forwardPath(drum, 0, '@open'), null);
  assert.equal(forwardPath(drum, 0, 'missing'), null);
  assert.throws(() => forwardPath(drum, -1, 'A'), RangeError);
});

test('every planned step is exactly one forward slot on drums of different lengths', () => {
  for (const flaps of [['', 'a', 'b'], ['', 'a', 'b', 'c', 'd', 'a', '@open']]) {
    const drum = createDrum('generic', { flaps });
    for (let from = 0; from < flaps.length; from++) for (const token of flaps.filter((item) => item !== '@open')) {
      let position = from;
      for (const next of forwardPath(drum, from, token)) {
        assert.equal(next, (position + 1) % flaps.length);
        position = next;
      }
      assert.equal(flaps[position], token);
    }
  }
});

test('an unavailable target holds the real flap rather than painting an invented value', async () => {
  const drum = createDrum('test', { flaps: ['', 'A'] });
  const module = { drum, index: 1 };
  let steps = 0;
  const motion = new MotionController([module], () => { steps++; });
  await motion.moveTo(['not printed']);
  assert.equal(module.index, 1);
  assert.equal(steps, 0);
});

test('interrupting motion settles forward and replans from the in-flight position', async () => {
  const drum = createDrum('test', { flaps: ['', 'A', 'B'] });
  const module = { drum, index: 0 };
  const trace = [];
  const motion = new MotionController([module], (cell, next, { signal }) => {
    cell.index = next;
    trace.push(next);
    if (trace.length === 1) return new Promise((resolve) => signal.addEventListener('abort', resolve, { once: true }));
    return Promise.resolve();
  });
  const first = motion.moveTo(['B']);
  const second = motion.moveTo(['']);
  assert.equal(await first, false);
  assert.equal(await second, true);
  assert.deepEqual(trace, [1, 2, 0]);
  assert.equal(module.index, 0);
});

test('engine accepts a board larger than the league build with a small unrelated drum', () => {
  const drums = { other: createDrum('other', { flaps: ['', 'X', 'Y'] }) };
  const layout = {
    rowHeight: 10, padding: 2, types: { square: { width: 10, flapWidth: 8, flapHeight: 8, faceWidth: 7 } },
    rows: Array.from({ length: 27 }, () => ({ modules: [{ type: 'square', drum: 'other' }] })),
  };
  validateLayout(layout, drums);
  const result = prepareFrame(Array.from({ length: 27 }, () => ['X']), layout, drums);
  assert.equal(result.targets.length, 27);
  assert.deepEqual(result.issues, []);
  assert.throws(() => prepareFrame(Array.from({ length: 28 }, () => ['X']), layout, drums));
  assert.throws(() => prepareFrame([['X', 'Y']], layout, drums));
  assert.equal(prepareFrame([['missing']], layout, drums).issues[0].state, 'missing');
});

test('Premier League uses the newer planned drum order and preserves every mockup view', () => {
  const drums = Object.fromEntries(Object.entries(app.drums).map(([id, definition]) => [id, createDrum(id, definition)]));
  validateLayout(app.layout, drums);
  assert.equal(app.layout.rows.length, 21);
  for (const drum of Object.values(drums)) {
    assert.equal(drum.flaps.length, 52);
    assert.equal(drum.flaps[0], '');
    assert.deepEqual(drum.flaps.slice(46), ['c:yellow', 'c:blue', 'c:orange', 'c:green', 'c:red', 'c:white']);
  }
  for (const id of ['name', 'digit', 'hname']) assert.equal(drums[id].flaps[45], '|divider');
  assert.equal(drums.hdigit.flaps.filter((item) => item === '@open').length, 7);
  const expected = ['pts', 'gd', 'gf', 'ga', 'pl', 'mov', 'zones', 'l1', 'l4g', 'l3', 'l4', 'l2', 'res', 'fix',
    'fa', 'fadraw', 'fafinal', 'lcsf', 'uclt', 'ucl', 'thu', 'cs', 'intl', 'off', 'pzone', 'pchamp',
    'pgoal', 'prain', 'pcheck', 'pflags'];
  for (const season of ['early', 'end']) for (const clock of ['24', '12']) {
    const views = app.createViews({ ...app.defaults, season, clock });
    assert.deepEqual(Object.keys(views), expected);
    for (const [id, view] of Object.entries(views)) {
      const model = view.build();
      assert(model.frames.length > 0);
      assert((model.still || 0) < model.frames.length);
      for (const frame of model.frames) {
        const result = prepareFrame(frame, app.layout, drums);
        assert.deepEqual(result.issues, [], id + ': every target must exist on its drum');
        assert.equal(result.targets.length, 63);
      }
    }
  }
});
