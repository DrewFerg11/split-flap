# Flap sets

What's printed on every flap of every drum for the Premier League display.

| File | What |
|---|---|
| [`flap-sets.md`](flap-sets.md) | **the one place to edit**: the rules, the per-drum lists, and the "All sets side by side" table |
| [`flap-sets.json`](flap-sets.json) | generated from that table: 4 drums × 52 entries, index = firmware flap number (0 = blank = home) |
| [`build_json.py`](build_json.py) | the generator: `python build_json.py`, or `--check` to fail if the JSON is out of date |

Change `flap-sets.md`, then run `python build_json.py` and commit both. The app firmware (#15) and the
site's [Premier League demo](https://drewferg11.github.io/split-flap/demo/premier-league/) should read
their drum lists from `flap-sets.json`, so the printed flaps, the firmware and the demo can't drift apart.
