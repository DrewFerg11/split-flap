# Instructions for AI coding agents

These rules apply to any AI agent (Claude, Codex/GPT, Copilot, others) working in this repository.
Human contributors: see [CONTRIBUTING.md](.github/CONTRIBUTING.md).

## Repository map

| Folder | What |
|---|---|
| `pcb/` | KiCad boards; fab packages built locally and committed |
| `hardware/` | physical parts (rail notes, part lists) |
| `firmware/` | module firmware, the controller (`lib/sfctl` + console), the shared bus protocol (`shared/sfbus.h`) |
| `applications/` | one folder per display application (`premier-league/`) |
| `docs/` | the Astro/Starlight site (GitHub Pages) and the browser demos |
| `tools/release/` | release packaging; process in [.github/RELEASING.md](.github/RELEASING.md) |
| `reference/` | a local working folder, git-ignored |

## This is an original design

Every split-flap display shares the same basic mechanism; within that, the modules, boards, firmware
and applications here were designed for this project. Treat and describe them as such:

- Write about what the design **is and does**, and why: dimensions, parts, behaviour, decisions,
  datasheets, our own tests.
- Acknowledgements of other projects are in [LICENSE.md](LICENSE.md); leave that section as it is
  unless asked.
- Compatibility with other hardware is stated as a plain fact (e.g. "the hall connector and pinout
  match the SplitFlap v5.1 board, so existing sensor leads plug in").

## Ignored paths

- `.gitignore` is authoritative. Never commit ignored paths, never use `git add -f`, and don't
  change `.gitignore` to publish something unless the owner asks for that specific path.
- `reference/` is a local scratch folder: don't copy from it or link to it.

## Before you commit

- Only commit your own work or material whose license allows it; say which in the PR.
- PR titles use Conventional Commits (`feat(firmware): …`, `docs: …`); the labeler reads them.
