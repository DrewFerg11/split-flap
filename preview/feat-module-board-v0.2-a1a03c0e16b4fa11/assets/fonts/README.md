# Local fonts

Downloaded 2026-11-08 from Google Fonts. These are unmodified WOFF2 Latin
subsets; Archivo is a variable font at normal width. They cover the mockup's
League Gothic 400, Archivo 400/500/700, and IBM Plex Mono 400/500.
Each family has its upstream OFL copyright and license text beside it.

| Local file | Source |
|---|---|
| archivo-latin-wght-normal.woff2 | https://fonts.gstatic.com/s/archivo/v25/k3kPo8UDI-1M0wlSV9XAw6lQkqWY8Q82sLydOxI.woff2 |
| ibm-plex-mono-latin-400-normal.woff2 | https://fonts.gstatic.com/s/ibmplexmono/v20/-F63fjptAgt5VM-kVkqdyU8n1i8q1w.woff2 |
| ibm-plex-mono-latin-500-normal.woff2 | https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3twJwlBFgg.woff2 |
| league-gothic-latin-400-normal.woff2 | https://fonts.gstatic.com/s/leaguegothic/v13/qFdR35CBi4tvBz81xy7WG7ep-BQAY7Krj7feObpH_9ahg9U.woff2 |

The stylesheet was requested with:

```text
https://fonts.googleapis.com/css2?family=League+Gothic&family=Archivo:wght@100..900&family=IBM+Plex+Mono:wght@400;500&display=swap
```

Use a modern browser user agent when refreshing it to obtain WOFF2 instead
of legacy TTF. Keep the Latin blocks, download their URLs, and point
`fonts.css` at the local filenames. Do not leave remote imports in CSS.
If a future app needs characters outside this subset, vendor the additional
subsets and declare their Unicode ranges.

License sources:

- https://github.com/google/fonts/blob/main/ofl/leaguegothic/OFL.txt
- https://github.com/google/fonts/blob/main/ofl/archivo/OFL.txt
- https://github.com/google/fonts/blob/main/ofl/ibmplexmono/OFL.txt

Standalone demos can load `../../assets/fonts/fonts.css`. Wait for
`document.fonts.ready` before measuring flap text.
