import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { resolve, join } from 'node:path';

export function getDemos(): { slug: string; title: string; description: string }[] {
  // npm runs Astro from docs/; import.meta.url moves when Astro bundles server modules.
  const directory = resolve('public/demo');
  return readdirSync(directory, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && existsSync(join(directory, entry.name, 'manifest.json')))
    .map((entry) => {
      if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(entry.name)) throw new Error('Invalid demo slug: ' + entry.name);
      const manifest = JSON.parse(readFileSync(join(directory, entry.name, 'manifest.json'), 'utf8'));
      if (typeof manifest.title !== 'string' || typeof manifest.description !== 'string' ||
          !existsSync(join(directory, entry.name, 'app.js'))) {
        throw new Error('Demo needs a title, description and app.js: ' + entry.name);
      }
      return { slug: entry.name, title: manifest.title, description: manifest.description };
    })
    .sort((a, b) => a.title.localeCompare(b.title));
}
