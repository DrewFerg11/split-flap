export async function createTextMetrics(config) {
  const font = '100px "' + config.family + '"';
  await document.fonts.load(font);
  if (!document.fonts.check(font)) throw new Error('The local display font could not be loaded.');
  const context = document.createElement('canvas').getContext('2d');
  context.font = font;
  const measure = (text) => context.measureText(text).width;
  const reference = config.reference;
  const fontSize = reference.width * 100 / (reference.squeeze * measure(reference.text));
  return {
    family: config.family, fontSize,
    squeeze(text, width) { return Math.min(1, width / (measure(text) / 100 * fontSize)); },
  };
}

export function createFlapRenderer(metrics, { colours = {}, icons = {} } = {}) {
  return function flap(item, type, { reference = false } = {}) {
    const face = document.createElement('div');
    face.className = 'sf-flap';
    face.title = item || 'blank';
    if (item === '@open') {
      if (reference) {
        face.classList.add('sf-open');
        face.textContent = 'open';
      }
    } else if (item === '|divider') {
      const bar = document.createElement('span');
      bar.className = 'sf-divider';
      face.append(bar);
    } else if (item.startsWith('c:')) {
      face.style.background = colours[item.slice(2)] || 'var(--sf-flap)';
    } else if (item.startsWith('#')) {
      // Icons are trusted app-owned SVG literals, never football API content.
      face.innerHTML = icons[item] || '';
    } else if (item) {
      const text = document.createElement('span');
      text.className = 'sf-text';
      text.textContent = item;
      text.style.setProperty('--fs', metrics.fontSize);
      text.style.setProperty('--sq', metrics.squeeze(item, item.length > 1 ? (type.multiFaceWidth || type.faceWidth) : type.faceWidth));
      face.append(text);
    }
    return face;
  };
}

// Cancelling a view change commits the in-flight step forward, then resolves.
export function stepFlap(module, next, { animate, signal }, renderFlap, duration) {
  const old = module.drum.flaps[module.index];
  const item = module.drum.flaps[next];
  module.index = next;
  module.element.dataset.index = String(next);
  module.element.setAttribute('aria-label', item === '@open' ? 'blank spare' : (item || 'blank'));
  const paint = () => module.shell.replaceChildren(renderFlap(item, module.type));
  if (!animate || signal.aborted) { paint(); return Promise.resolve(); }
  return new Promise((resolve) => {
    const fixed = document.createElement('div');
    fixed.className = 'sf-fixed-bottom sf-half';
    fixed.append(renderFlap(old, module.type));
    const leaf = document.createElement('div');
    leaf.className = 'sf-leaf';
    for (const [side, text] of [['front', old], ['back', item]]) {
      const half = document.createElement('div');
      half.className = 'sf-half sf-' + side;
      half.append(renderFlap(text, module.type));
      leaf.append(half);
    }
    module.shell.replaceChildren(renderFlap(item, module.type), fixed, leaf);
    const animation = leaf.animate([{ transform: 'rotateX(0)' }, { transform: 'rotateX(-180deg)' }],
      { duration, easing: 'linear', fill: 'forwards' });
    const finish = () => {
      signal.removeEventListener('abort', finish);
      animation.onfinish = null;
      animation.oncancel = null;
      paint();
      animation.cancel();
      resolve();
    };
    animation.onfinish = finish;
    signal.addEventListener('abort', finish, { once: true });
  });
}
