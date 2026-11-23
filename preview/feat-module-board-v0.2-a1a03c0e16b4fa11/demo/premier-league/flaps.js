// Translate application data into the shared renderer's token format.
export function loadDrums(source, { colours, icons, wildcards }) {
  const definitions = [['name', 'name', 'Main name'], ['digit', 'digit', 'Main digit'],
    ['header_name', 'hname', 'Header name'], ['header_digit', 'hdigit', 'Header digit']];
  if (!Number.isInteger(source.flaps) || source.flaps < 1) throw new Error('Invalid flap count');
  return Object.fromEntries(definitions.map(([key, id, label]) => {
    const entries = source.drums?.[key];
    if (!Array.isArray(entries) || entries.length !== source.flaps) throw new Error('Invalid drum: ' + key);
    let wildcard = 0;
    const flaps = entries.map((entry) => {
      switch (entry.kind) {
        case 'blank': return '';
        case 'open': return '@open';
        case 'divider': return '|divider';
        case 'text':
          if (typeof entry.text === 'string' && entry.text.length) return entry.text;
          break;
        case 'colour':
          if (Object.hasOwn(colours, entry.colour)) return 'c:' + entry.colour;
          break;
        case 'symbol': {
          const symbol = entry.symbol === 'wildcard' ? wildcards[key]?.[wildcard++]
            : entry.symbol === 'pl-lion' ? 'lion' : entry.symbol;
          if (Object.hasOwn(icons, '#' + symbol)) return '#' + symbol;
          break;
        }
      }
      throw new Error('Unsupported flap in ' + key + ': ' + JSON.stringify(entry));
    });
    return [id, { label, flaps }];
  }));
}
