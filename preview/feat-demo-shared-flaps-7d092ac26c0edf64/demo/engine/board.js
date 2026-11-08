import { validateLayout } from './drums.js';
import { MotionController } from './motion.js';
import { stepFlap } from './flap.js';

export function createBoard(container, layout, drums, renderFlap, stepMs) {
  validateLayout(layout, drums);
  const outer = document.createElement('div');
  outer.className = 'sf-boardouter';
  const labels = document.createElement('div');
  labels.className = 'sf-rownums';
  labels.setAttribute('aria-hidden', 'true');
  const board = document.createElement('div');
  board.className = 'sf-board';
  board.setAttribute('role', 'table');
  board.setAttribute('aria-label', 'Split-flap display');
  board.style.setProperty('--row-height', layout.rowHeight);
  board.style.setProperty('--board-padding', layout.padding);
  const modules = [];
  for (const [rowIndex, row] of layout.rows.entries()) {
    const label = document.createElement('span');
    label.textContent = row.label ?? String(rowIndex + 1);
    labels.append(label);
    const line = document.createElement('div');
    line.className = 'sf-row' + (row.header ? ' sf-header-row' : '');
    line.setAttribute('role', 'row');
    for (const [column, spec] of row.modules.entries()) {
      const type = layout.types[spec.type];
      const drum = drums[spec.drum];
      const element = document.createElement('div');
      element.className = 'sf-module';
      element.setAttribute('role', 'cell');
      element.setAttribute('aria-label', drum.flaps[drum.home] || 'blank');
      element.dataset.drum = drum.id;
      element.dataset.index = String(drum.home);
      element.dataset.row = String(rowIndex);
      element.dataset.column = String(column);
      for (const [key, value] of Object.entries({ width: type.width, 'flap-width': type.flapWidth, 'flap-height': type.flapHeight })) {
        element.style.setProperty('--' + key, value);
      }
      const shell = document.createElement('div');
      shell.className = 'sf-flap-shell';
      shell.append(renderFlap(drum.flaps[drum.home], type));
      element.append(shell);
      line.append(element);
      modules.push({ element, shell, type, drum, index: drum.home, row: rowIndex, column });
    }
    board.append(line);
  }
  outer.append(labels, board);
  container.append(outer);
  const motion = new MotionController(modules,
    (module, next, options) => stepFlap(module, next, options, renderFlap, stepMs));
  const height = layout.rows.length * layout.rowHeight + layout.padding * 2;
  const width = Math.max(...layout.rows.map((row) => row.modules.reduce((sum, spec) => sum + layout.types[spec.type].width, 0))) + layout.padding * 2;
  let zoom = 'fit';
  const scale = () => {
    const byWidth = Math.max(1, container.clientWidth - 38) / width;
    const value = zoom === 'fit' ? Math.min(byWidth, Math.max(200, window.innerHeight - 80) / height, 1.2) : Math.min(byWidth, 2.2);
    outer.style.setProperty('--u', value);
    labels.style.setProperty('--row-height', layout.rowHeight);
    labels.style.setProperty('--board-padding', layout.padding);
  };
  const observer = new ResizeObserver(scale);
  observer.observe(container);
  window.addEventListener('resize', scale);
  scale();
  return {
    motion, modules,
    setZoom(value) { zoom = value; scale(); },
    destroy() { motion.stop(); observer.disconnect(); window.removeEventListener('resize', scale); },
  };
}
