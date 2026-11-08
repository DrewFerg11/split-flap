import { readFile, writeFile } from 'node:fs/promises';

// Resolve from this file so generation is independent of the caller's cwd.
const source = new URL('../../applications/premier-league/flap-sets/flap-sets.json', import.meta.url);
const destination = new URL('../public/demo/premier-league/flap-sets.generated.js', import.meta.url);
const data = JSON.parse(await readFile(source, 'utf8'));
await writeFile(destination, '// Generated from applications/premier-league/flap-sets/flap-sets.json; do not edit.\n'
  + 'export default ' + JSON.stringify(data, null, 2) + ';\n');
