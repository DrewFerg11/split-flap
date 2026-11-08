// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// One URL controls every generated link, asset path, canonical URL and sitemap.
// The deploy workflow sets it to the branch preview's full URL before building.
const buildUrl = new URL(process.env.SITE_BUILD_URL || 'https://drewferg11.github.io/split-flap/');
const base = buildUrl.pathname.replace(/\/?$/, '/');
const preview = process.env.SPLIT_FLAP_PREVIEW === '1';

export default defineConfig({
  site: buildUrl.origin,
  base,
  trailingSlash: 'always',
  integrations: [
    starlight({
      title: 'Split-flap',
      description: 'Build a modular split-flap display: printable parts, custom electronics, firmware, and applications.',
      favicon: '/favicon.svg',
      disable404Route: true,
      customCss: ['./src/styles/extra.css'],
      social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/DrewFerg11/split-flap' }],
      head: [
        { tag: 'link', attrs: { rel: 'stylesheet', href: base + 'assets/fonts/fonts.css' } },
        ...(preview ? [{ tag: /** @type {'meta'} */ ('meta'), attrs: { name: 'robots', content: 'noindex, nofollow' } }] : []),
      ],
      sidebar: [
        { label: 'The project', slug: 'guide/overview' },
        { label: 'Display demos', slug: 'demo' },
        // Starlight adds Astro's base to sidebar links; prefixing base here would duplicate it.
        { label: 'Premier League demo', link: '/demo/premier-league/' },
        { label: 'Firmware', slug: 'guide/firmware' },
      ],
    }),
  ],
});
