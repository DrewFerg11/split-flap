# Maintaining the Pages site

Astro + Starlight lives entirely in this directory, independently of firmware.
With Node.js 24 or newer, from this directory:

```sh
npm ci
npm run dev
```

The server prints its URL, including the `/split-flap/` base path.
Before opening a PR:

```sh
npm run check
npm run test:previews
npm run test:demo
npm run build
npm run verify
```

`check` checks source types and content schemas. `build` creates the static
site and local search index in `dist/`. `verify` checks generated links,
local resources, indexing tags, canonical URLs, the sitemap, and reserved
deployment paths. Use `npm run preview` to inspect the exported site.

## Editing and extending

- Write guides in `src/content/docs/` as Markdown. Use MDX for pages that
  need Starlight's built-in cards, grids, tabs, or steps.
- Update the sidebar in `astro.config.mjs` when adding a guide.
- The homepage is `src/content/docs/index.mdx`; its image is the project's own
  KiCad render at `../pcb/module-board/fab/images/league-table-module-v0.1-3d.png`.
  The workflow watches that source image too. Theme adjustments live in `src/styles/extra.css`.
  Prefer Starlight components to custom replacements.
- Add demos under `public/demo/<slug>/` with a `manifest.json` (title and
  description) and `app.js`. Astro copies the ES modules unchanged, and the
  generic route and demo list discover the manifest automatically. Reuse
  `public/demo/engine/` for board rendering, font metrics, validation, and
  forward-only motion. See the Premier League folder's README for port notes.
- `npm run test:demo` checks drum traversal, interruptions, unknown targets,
  a board larger than 20 rows, and every Premier League view in both seasons
  and clock modes. The engine has no league-specific names or row counts.
- `public/assets/fonts/fonts.css` provides local fonts for the site and demos.
  Keep their license texts and third-party notices.
- Keep runtime resources local: no remote fonts, scripts, analytics, or APIs.
- Firmware documentation lives at `guide/firmware/`. A browser flasher can
  be linked from that page when ready.

Dependencies are pinned in `package.json` and `package-lock.json`.
Commit both files when updating them. Output, dependencies, and caches are ignored.

## Publishing and previews

`Docs / Deploy` builds pushes to `main`, `docs/**`, `feat/**`, and
`feature/**`, plus PRs that change site inputs. Fork PRs and PRs from other
branch prefixes build without deploying. Manual runs are also available.
Actions are pinned by commit; update their version comments with the pins.

Main replaces the site root on `gh-pages`. Supported preview branches publish
to `preview/<sanitised-branch>-<hash>/`. The readable portion is capped at
80 characters; a 16-character SHA-256 suffix of the original branch name
distinguishes names such as `feat/a-b` and `feat/a/b`. Both workflows use
the same mapping, checked by `npm run test:previews`.
Same-repository PRs receive one sticky preview
comment after a successful deployment.

`SITE_BUILD_URL` sets the full output URL, including the preview base path.
`SPLIT_FLAP_PREVIEW=1` adds `noindex, nofollow` to preview pages.
The 404 page always has `noindex` and uses links that work at any depth.

To test a preview, set these variables in your shell and run the same build
and verification commands:

```text
SITE_BUILD_URL=https://drewferg11.github.io/split-flap/preview/feat-example/
SPLIT_FLAP_PREVIEW=1
```

Unset them before rebuilding production output. The workflow sets them
automatically; no source edits are needed for previews.

Deploy and cleanup must use identical branch prefixes and sanitisers.
`Docs / Cleanup preview` removes a preview when its branch is deleted.
GitHub runs it from the default branch, so deletion testing must wait until
it is merged. Both workflows retry pushes against the latest tip.

Main deployments preserve `preview/`, `.nojekyll`, and `firmware/`.
`firmware/` is reserved for binaries and the future flasher's `index.json`;
never put generated documentation at that deployment path.

### One-time owner setup

1. Create an orphan `gh-pages` branch with `.nojekyll` and a placeholder `index.html`.
2. In Settings → Pages, select **Deploy from a branch**, **gh-pages**, **/ (root)**.
3. Run `Docs / Deploy` on `main` and the preview branch.

Until `gh-pages` exists, deployment skips with a notice after a successful build.
The publishing branch and Pages settings were configured on 2026-11-08.
