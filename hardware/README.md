# hardware/

3D-printable and physical parts: enclosures, drums, flaps, mounts, and anything else that
isn't a PCB (boards live in [`pcb/`](../pcb/)). One folder per part:

```
hardware/<part>/
  source/     native CAD, generation scripts, parameters
  exports/    STEP / STL / 3MF matching the source
  README.md
```

**Releases:** tagged `hw/<part>/vX.Y`, built locally, files committed. Print files may also be
published on MakerWorld and linked from the release.

| Path | What |
|---|---|
| [`rail/`](rail/) | the trunk up the side of the board: 12 V + bus to every row (research, leaning to idea A) |
| [`parts-shortlist.md`](parts-shortlist.md) | module parts: the N20 encoder motor and its sources |

The digit and name modules (CAD, generation scripts, print files) live in `modules/`, which is
**git-ignored for now**: it's kept on the development machine until it's decided how the 3D model
files are distributed. Nothing released yet.
