# Releasing

Every release is a tag. Pushing the tag runs [`workflows/release.yml`](workflows/release.yml),
which waits for the admin's approval and then publishes the GitHub release.

## Tags

`<type>/<component>/v<version>`, one tag family per component:

| Type | Folder | Version | Files | Example |
|---|---|---|---|---|
| `pcb` | `pcb/<board>/` | `vX.Y` (matches the silkscreen) | built locally, committed | `pcb/module-board/v0.1` |
| `hw` | `hardware/<part>/` | `vX.Y` | built locally, committed (may link to MakerWorld) | `hw/digit-module/v1.0` |
| `fw` | `firmware/<target>/` | `vX.Y.Z` | **built by CI** from the tagged source | `fw/module/v1.4.2` |
| `app` | `applications/<app>/` | `vX.Y.Z` | **built by CI** from the tagged source | `app/premier-league-table/v1.0.0` |

- Any `v0.x` publishes as a **pre-release**. `fw`/`app` can also add `-rc.N`
  (`fw/module/v1.5.0-rc.1`, also a pre-release); `pcb`/`hw` can't, since each version is a
  physical revision.
- No release is ever marked GitHub "Latest" (one per repo can't serve several components).
  Firmware downloads go through the web flasher's own index.
- Never create a bare `pcb/module-board` tag: git can't hold it next to `pcb/module-board/v0.1`.
- Never move or reuse a published tag. To redo a release, delete the release and tag, fix, and
  tag a new version (or the same one, if nobody has downloaded it).

## Per component

Two files in the component folder:

- **`release.toml`**: what ships: name, `asset_prefix`, `[[assets]]` (committed files, renamed
  to `<prefix>-v<version>-<name>` on upload), `[[images]]`, `[[checks]]` (`kicad-erc`,
  `kicad-drc`), `[specs]`, `[order]`, `[links]`. `fw`/`app` add a `[build]` table
  (PlatformIO envs + artifacts); `pcb`/`hw` must not have one.
  Example: [`pcb/module-board/release.toml`](../pcb/module-board/release.toml).
- **`RELEASE-NOTES.md`**: this release only. TOML front matter between `+++` lines (`version`,
  `status`, `status_details`, `prerelease_note`, `[bringup]` = pass/fail/pending/n/a, and for
  apps `[tested_with]` = component → tag), then `## Summary` (required) and any other `##`
  sections (`## Known issues`, ...), which are copied in as written.

The release page layout is fixed per type in [`tools/release/templates/`](../tools/release/templates/),
so every release of a type looks the same. Firmware and app releases also get an automatic
change list since the previous tag of the same component.

## Steps

1. **Build locally** (`pcb`/`hw` only): run the component's build, check the outputs, commit
   them. For a PCB: ERC/DRC reports in `fab/` at 0 errors.
2. **Update** `release.toml` if the file list changed, and write `RELEASE-NOTES.md` with the
   new version.
3. **Preview**: `python tools/release/release.py preview <tag>` runs every gate (and, for
   `fw`/`app`, a fresh PlatformIO build) and writes `dist/notes.md` + `dist/assets/` exactly as
   the release will get them (links point at HEAD).
4. **Merge** to `main` through a PR.
5. **Tag** the merge commit on `main` and push the tag:
   ```
   git switch main && git pull
   git tag -a pcb/module-board/v0.1 -m "Module board v0.1"
   git push origin pcb/module-board/v0.1
   ```
6. **Approve** the run in Actions (the `publish` job waits on the `release` environment).
7. **Check** the release page.

## What CI checks before publishing

- Tag format, and the version shape for its type.
- `build` and `publish` use the exact commit `check` gated. The tag is re-read from GitHub just
  before and after the release is created; if it moved, publish fails (and deletes the release).
- `release.toml` exists and names the same component; `RELEASE-NOTES.md` version = tag version.
- Every asset and image exists, isn't empty, and isn't an unfetched LFS pointer.
- ERC/DRC reports show 0 errors (DRC warnings allowed), 0 unconnected pads.
- The tagged commit is on `main`.
- `app` releases: every `tested_with` tag exists.

## Repo settings this relies on

- Environment **`release`**: required reviewer = the admin; self-review allowed; deployments
  only from the four tag patterns.
- Ruleset **release tags**: `refs/tags/{pcb,hw,fw,app}/**/*` can only be created, moved or
  deleted by admins.
