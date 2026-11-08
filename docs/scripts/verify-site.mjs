// Checks properties of the exported site that a successful Astro build cannot guarantee.
import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { resolve, relative, sep } from 'node:path';

const output = resolve('dist');
const site = new URL(process.env.SITE_BUILD_URL || 'https://drewferg11.github.io/split-flap/');
const preview = process.env.SPLIT_FLAP_PREVIEW === '1';
const base = site.pathname.replace(/\/?$/, '/');
const walk = (dir) => readdirSync(dir).flatMap((name) => {
  const path = resolve(dir, name);
  return statSync(path).isDirectory() ? walk(path) : [path];
});
const files = walk(output);
const html = files.filter((path) => path.endsWith('.html'));
assert(html.length >= 5, 'Expected the home page, three guides, and a 404');
for (const reserved of ['preview', 'firmware', '.nojekyll']) {
  assert(!existsSync(resolve(output, reserved)), 'Build must not overwrite reserved path: ' + reserved);
}
for (const path of html) {
  const name = relative(output, path).split(sep).join('/');
  const content = readFileSync(path, 'utf8');
  const pageUrl = new URL(name === 'index.html' ? '' : name.replace(/index\.html$/, ''), site);
  const noindex = /<meta\b[^>]*name="robots"[^>]*content="[^"]*noindex/.test(content);
  assert.equal(noindex, preview || name === '404.html', name + ': wrong indexing policy');
  if (name !== '404.html') {
    const canonical = content.match(/<link\b[^>]*rel="canonical"[^>]*href="([^"]+)"/)?.[1];
    assert.equal(canonical, pageUrl.href, name + ': wrong canonical URL');
  }
  for (const match of content.matchAll(/<(a|link|script|img|source|iframe)\b[^>]*>/g)) {
    const tag = match[1];
    const markup = match[0];
    const value = markup.match(/\b(?:href|src)="([^"]+)"/)?.[1];
    if (!value || value.startsWith('#') || /^(data:|mailto:|tel:)/.test(value)) continue;
    const url = new URL(value.replaceAll('&amp;', '&'), pageUrl);
    if (url.origin !== site.origin) {
      assert(tag === 'a' || (tag === 'link' && /rel="(?:canonical|alternate)"/.test(markup)),
        name + ': third-party resource ' + value);
      continue;
    }
    assert(url.pathname.startsWith(base), name + ': link escapes site base: ' + value);
    if (tag === 'link' && /rel="(?:canonical|alternate)"/.test(markup)) continue;
    const target = resolve(output, decodeURIComponent(url.pathname.slice(base.length)));
    assert(target === output || target.startsWith(output + sep), 'Path escapes build output');
    assert(existsSync(target), name + ': missing local link/resource ' + value);
    if (statSync(target).isDirectory()) {
      assert(existsSync(resolve(target, 'index.html')), name + ': missing index for ' + value);
    }
  }
}
const sitemap = readFileSync(resolve(output, 'sitemap-0.xml'), 'utf8');
assert(!sitemap.includes('/404'), '404 must be excluded from sitemap');
for (const [, location] of sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)) {
  assert(location.startsWith(site.href), 'Sitemap escapes build base: ' + location);
}
const fonts = resolve(output, 'assets/fonts');
for (const [, file] of readFileSync(resolve(fonts, 'fonts.css'), 'utf8').matchAll(/url\("([^"]+)"\)/g)) {
  const bytes = readFileSync(resolve(fonts, file));
  assert.equal(bytes.subarray(0, 4).toString(), 'wOF2', 'Invalid font: ' + file);
}
assert(existsSync(resolve(output, 'pagefind/pagefind.js')), 'Missing local search index');
console.log('Verified ' + html.length + ' pages: links, assets, canonical URLs, indexing, sitemap, local fonts, and search.');
