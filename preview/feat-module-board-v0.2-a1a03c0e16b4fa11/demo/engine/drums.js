export function createDrum(id, definition) {
  if (!Array.isArray(definition.flaps) || !definition.flaps.length ||
      definition.flaps.some((flap) => typeof flap !== 'string')) {
    throw new Error('Drum ' + id + ' needs a nonempty list of string flaps.');
  }
  return {
    id, label: definition.label || id,
    flaps: Object.freeze([...definition.flaps]),
    proposed: new Set(definition.proposed || []),
    home: Math.max(0, definition.flaps.indexOf('')),
  };
}

// Duplicate printed items are distinct positions: choose the nearest forward copy.
export function forwardPath(drum, current, target) {
  if (!Number.isInteger(current) || current < 0 || current >= drum.flaps.length) {
    throw new RangeError('Current position is outside drum ' + drum.id);
  }
  if (target === '@open') return null; // A spare position is not a selectable item.
  for (let steps = 0; steps < drum.flaps.length; steps++) {
    if (drum.flaps[(current + steps) % drum.flaps.length] === target) {
      return Array.from({ length: steps }, (_, index) => (current + index + 1) % drum.flaps.length);
    }
  }
  return null;
}

export function validateLayout(layout, drums) {
  if (!layout.rows?.length || !(layout.rowHeight > 0) || !(layout.padding >= 0)) {
    throw new Error('A board needs rows and positive physical dimensions.');
  }
  for (const row of layout.rows) {
    if (!row.modules?.length) throw new Error('Every row needs at least one module.');
    for (const module of row.modules) {
      const type = layout.types[module.type];
      if (!drums[module.drum] || !type || !['width', 'flapWidth', 'flapHeight', 'faceWidth'].every((key) => type[key] > 0)) {
        throw new Error('Unknown drum, module type, or invalid dimensions.');
      }
    }
  }
}

export function prepareFrame(frame, layout, drums) {
  if (!Array.isArray(frame) || frame.length > layout.rows.length) throw new Error('View exceeds board row capacity.');
  const targets = [];
  const issues = [];
  layout.rows.forEach((row, rowIndex) => {
    const values = frame[rowIndex] || [];
    if (!Array.isArray(values) || values.length > row.modules.length) throw new Error('View exceeds module column capacity.');
    row.modules.forEach((module, column) => {
      const item = values[column] ?? '';
      if (typeof item !== 'string') throw new Error('View cells must contain flap strings.');
      const drum = drums[module.drum];
      const available = item !== '@open' && drum.flaps.includes(item);
      targets.push(item);
      if (!available) issues.push({
        row: rowIndex, column, drum: drum.id, item,
        state: drum.proposed.has(item) ? 'proposed' : 'missing',
      });
    });
  });
  return { targets, issues };
}
