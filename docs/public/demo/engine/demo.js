import { createDrum, prepareFrame } from './drums.js';
import { createTextMetrics, createFlapRenderer } from './flap.js';
import { createBoard } from './board.js';

const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};

export async function mountDemo(root, app) {
  const drums = Object.fromEntries(Object.entries(app.drums).map(([id, drum]) => [id, createDrum(id, drum)]));
  const metrics = await createTextMetrics(app.typography);
  const renderFlap = createFlapRenderer(metrics, app);
  const state = { ...app.defaults };
  const storageKey = 'split-flap-demo:' + app.id;
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(storageKey) || '{}') || {}; } catch {}
  for (const option of app.options) {
    if (option.values.some(([value]) => saved[option.id] === value)) state[option.id] = saved[option.id];
  }
  const views = app.createViews(state);
  if (Object.hasOwn(views, saved.view)) state.view = saved.view;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  if (reduced.matches) state.anim = 'off';
  const save = () => { try { localStorage.setItem(storageKey, JSON.stringify(state)); } catch {} };
  root.classList.add('sf-demo');
  root.replaceChildren();
  root.style.setProperty('--sf-flap-font', '"' + metrics.family + '"');
  const lede = el('p', 'sf-lede', app.description);
  const controls = el('div', 'sf-controls');
  controls.setAttribute('role', 'group');
  controls.setAttribute('aria-label', 'Display views and options');
  const groups = {};
  for (const [id, label] of app.groups) {
    const group = el('div', 'sf-control-group');
    group.append(el('span', 'sf-control-label', label));
    controls.append(group);
    groups[id] = group;
  }
  const options = el('div', 'sf-options');
  controls.append(options);
  const main = el('div', 'sf-main');
  const boardColumn = el('div', 'sf-boardcol');
  const side = el('div', 'sf-side');
  const card = (title) => {
    const node = el('section', 'sf-card');
    node.append(el('h2', '', title));
    side.append(node);
    return node;
  };
  const viewCard = card('View');
  const viewTitle = el('h3');
  const caption = el('p');
  const stats = el('p', 'sf-stat');
  stats.setAttribute('role', 'status');
  stats.setAttribute('aria-live', 'polite');
  viewCard.append(viewTitle, caption, stats);
  const neededCard = card('Flaps this view needs');
  const needed = el('div');
  neededCard.append(needed);
  for (const note of app.notes || []) {
    const node = card(note.title);
    node.append(el('p', '', note.text));
    if (note.table) {
      const table = el('table');
      const head = el('thead');
      const headings = el('tr');
      note.table.columns.forEach((title) => headings.append(el('th', '', title)));
      head.append(headings);
      const body = el('tbody');
      note.table.rows.forEach((row) => {
        const line = el('tr');
        row.forEach((value) => line.append(el('td', '', String(value))));
        body.append(line);
      });
      table.append(head, body);
      node.append(table);
    }
  }
  const squeezeCard = card('Long flaps');
  squeezeCard.append(el('p', '', app.typography.description));
  const squeezed = new Map();
  for (const row of app.layout.rows) for (const spec of row.modules) {
    const type = app.layout.types[spec.type];
    if (!type.showSqueeze) continue;
    for (const text of drums[spec.drum].flaps) {
      if (!text || /^[c:#@|]/.test(text)) continue;
      const ratio = metrics.squeeze(text, text.length > 1 ? (type.multiFaceWidth || type.faceWidth) : type.faceWidth);
      if (ratio < 0.999) squeezed.set(text, Math.min(squeezed.get(text) ?? 1, ratio));
    }
  }
  const squeezeList = el('ul', 'sf-squeeze-list');
  [...squeezed].sort((a, b) => a[1] - b[1]).forEach(([text, ratio]) =>
    squeezeList.append(el('li', '', text + ' · ' + Math.round(ratio * 100) + '%')));
  squeezeCard.append(squeezeList);
  main.append(boardColumn, side);
  const reference = el('section', 'sf-sets');
  reference.append(el('h2', '', 'Drum reference'));
  for (const [id, drum] of Object.entries(drums)) {
    const group = el('section');
    group.append(el('h3', '', drum.label + ' · ' + drum.flaps.length + ' flaps'));
    const grid = el('div', 'sf-setgrid');
    const spec = app.layout.rows.flatMap((row) => row.modules).find((module) => module.drum === id);
    if (!spec) continue;
    const type = app.layout.types[spec.type];
    drum.flaps.forEach((item, index) => {
      const cell = el('div', 'sf-set-cell');
      cell.style.setProperty('--flap-width', type.flapWidth);
      cell.style.setProperty('--flap-height', type.flapHeight);
      cell.append(el('span', 'sf-slot', String(index + 1).padStart(2, '0')));
      cell.append(renderFlap(item, type, { reference: true }));
      grid.append(cell);
    });
    group.append(grid);
    reference.append(group);
  }
  root.append(lede, controls, main, reference);
  const board = createBoard(boardColumn, app.layout, drums, renderFlap, app.stepMs || 35);
  let generation = 0;
  let timer;
  const buttons = [];
  const optionButtons = [];
  for (const [id, view] of Object.entries(views)) {
    const button = el('button', '', view.label);
    button.type = 'button';
    button.dataset.view = id;
    button.addEventListener('click', () => { state.view = id; save(); render(); });
    groups[view.g].append(button);
    buttons.push(button);
  }
  for (const option of app.options) {
    const group = el('div', 'sf-option-group');
    group.append(el('span', 'sf-control-label', option.label));
    for (const [value, label] of option.values) {
      const button = el('button', '', label);
      button.type = 'button';
      button.dataset.option = option.id;
      button.dataset.value = value;
      button.addEventListener('click', () => { state[option.id] = value; save(); render(); });
      group.append(button);
      optionButtons.push(button);
    }
    options.append(group);
  }

  function requirements(model, prepared) {
    needed.replaceChildren();
    const issues = new Map();
    prepared.forEach((frame) => frame.issues.forEach((issue) => issues.set(issue.drum + '\0' + issue.item, issue)));
    needed.append(el('p', 'sf-validation', issues.size
      ? issues.size + ' unavailable target(s). Those modules hold their actual flap.'
      : 'All target flaps are present in the configured drums.'));
    issues.forEach((issue) => needed.append(el('p', 'sf-issue',
      drums[issue.drum].label + ': ' + (issue.item || 'blank') + ' (' + issue.state + ')')));
    for (const [id, drum] of Object.entries(drums)) {
      const items = new Set();
      model.frames.forEach((frame) => app.layout.rows.forEach((row, rowIndex) =>
        row.modules.forEach((spec, column) => {
          if (spec.drum === id) items.add(frame[rowIndex]?.[column] ?? '');
        })));
      const details = el('details');
      details.append(el('summary', '', drum.label + ' · ' + items.size + ' distinct targets'));
      const list = el('ul', 'sf-needed-list');
      items.forEach((item) => {
        const positions = drum.flaps.flatMap((token, index) => token === item && token !== '@open' ? [index + 1] : []);
        list.append(el('li', '', (item || 'blank') + ' · ' + (positions.length ? 'slot ' + positions.join(', ') : 'unavailable')));
      });
      details.append(list);
      needed.append(details);
    }
  }

  function render() {
    const current = ++generation;
    clearTimeout(timer);
    board.motion.stop();
    const view = views[state.view];
    const model = view.build();
    if (!model.frames?.length) throw new Error('A view needs at least one frame.');
    const prepared = model.frames.map((frame) => prepareFrame(frame, app.layout, drums));
    const animate = state.anim === 'on' && !reduced.matches;
    root.classList.toggle('sf-hide-checks', state.marks === 'off');
    board.setZoom(state.zoom);
    viewTitle.textContent = view.title;
    caption.textContent = model.caption || '';
    buttons.forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.view === state.view)));
    optionButtons.forEach((button) => {
      button.setAttribute('aria-pressed', String(state[button.dataset.option] === button.dataset.value));
      button.disabled = (button.dataset.option === 'season' && !view.seasonal) ||
        (button.dataset.option === 'anim' && button.dataset.value === 'on' && reduced.matches);
    });
    requirements(model, prepared);
    let frame = animate ? 0 : (model.still || 0);
    const show = async () => {
      const occupied = model.frames[frame].filter((row) => row.some((item) => item !== '')).length;
      stats.textContent = occupied + ' of ' + app.layout.rows.length + ' rows used · frame ' +
        (frame + 1) + '/' + prepared.length + (animate ? ' · forward-only motion' : ' · still');
      root.dataset.frame = String(frame);
      root.dataset.view = state.view;
      root.dataset.moving = 'true';
      const completed = await board.motion.moveTo(prepared[frame].targets, { animate });
      if (current !== generation) return;
      root.dataset.moving = 'false';
      if (completed && animate && prepared.length > 1) {
        timer = setTimeout(() => { frame = (frame + 1) % prepared.length; show(); }, model.ms || 700);
      }
    };
    show();
  }
  const reduceChanged = () => { if (reduced.matches) state.anim = 'off'; render(); };
  reduced.addEventListener('change', reduceChanged);
  const suspend = () => { ++generation; clearTimeout(timer); board.motion.stop(); };
  const visibility = () => { document.hidden ? suspend() : render(); };
  document.addEventListener('visibilitychange', visibility);
  render();
  return () => {
    suspend();
    board.destroy();
    reduced.removeEventListener('change', reduceChanged);
    document.removeEventListener('visibilitychange', visibility);
  };
}
