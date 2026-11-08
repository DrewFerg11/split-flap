# Premier League demo

Views and invented samples are ported from Drew's confirmed local mockup,
board-mockup.html (last modified 2026-10-24).
Source SHA-256: e451520dbd4346f65a1feafb828e8aa7123f3771cc8f8368fa44b93b50a6368c.

data.js holds samples; views.js holds views; config.js holds the physical
layout and drum lists; app.js mounts the shared engine.
Drum order follows the newer flap-set notes (2026-11-05), as requested:
main-name, main-digit, and header-name dividers are at slot 46, directly
before the six colours. Header digits retain the notes' three repeated
13-item blocks and seven spares; no divider is printed on that drum.
All four lists have 52 entries. UI counts come from list lengths.

The Astro route discovers this folder from manifest.json. A second app needs
only a new sibling folder with manifest, config, views/data, and app.js. It
can use a different row count, columns, physical sizes, and drum lengths.

When updating the mockup, change the app files rather than adding league
logic to ../engine/. All original views are covered by app validation tests.
Stale captions claiming GOALS FOR/AGAINST were missing header flaps have been
corrected. Text-only LION and LIVER placeholders are preserved. No club
crests or league logos are distributed.

TODO: replace drum definitions in config.js with application-owned data from
applications/premier-league once the flap sets are migrated. That is the
single switching point; printed flap data must eventually be authoritative.
