# split-flap
3D-printable split-flap modules, electronics, and firmware

## Layout

| Folder | What | Release tag |
|---|---|---|
| [`pcb/`](pcb/) | KiCad boards; fab packages built locally and committed | `pcb/<board>/vX.Y` |
| [`hardware/`](hardware/) | 3D-printable and physical parts | `hw/<part>/vX.Y` |
| [`firmware/`](firmware/) | Shared module and controller firmware; built by CI | `fw/<target>/vX.Y.Z` |
| [`applications/`](applications/) | Displays built from the above (e.g. Premier League) | `app/<application>/vX.Y.Z` |

## License

Free to build, modify, and share for noncommercial use under
[CC BY-NC-SA 4.0](LICENSE.md), with a few extra permissions (paying a fab for your own
build, selling a used personal build, platform rewards on remixes). Commercial use needs
permission. See [LICENSE.md](LICENSE.md), [THIRD-PARTY-NOTICES.md](LICENSES/THIRD-PARTY-NOTICES.md),
and [CONTRIBUTING.md](.github/CONTRIBUTING.md).
