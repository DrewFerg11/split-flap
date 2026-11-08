# applications/

Displays built from the shared hardware, PCBs and firmware, one folder per application. An
application holds its own controller build, configuration and flap sets; it uses the shared parts
(the default controller in [`firmware/controller/`](../firmware/), the module firmware, the boards)
rather than copying them.

| Folder | What |
|---|---|
| [`premier-league/`](premier-league/) | Premier League (EPL): table and live scores. Concept, plan, flap sets; firmware planned (#15) |

## Naming

One slug per application, used for the folder, the release tag (`app/<slug>/vX.Y.Z`) and
`component` in its `release.toml`: lowercase, hyphens, and whatever people call the league:
`premier-league`, `nfl`, `nba`, `mls`. One app per league; table, live scores and fixtures are
modes inside it. The full name with its abbreviation, e.g. "Premier League (EPL)", goes in the
manifest's `name` (the release title) and the app's README.

**Releases:** CI builds the firmware from the tagged source, and each release lists the exact
`pcb/`, `hw/` and `fw/` versions it was tested with.
