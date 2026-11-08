# firmware/

Shared firmware: the per-module firmware (motion, homing, calibration, RS-485) and controller
code reused by every application. Application-specific builds live in
[`applications/`](../applications/).

**Releases:** tagged `fw/<target>/vX.Y.Z`. CI builds every firmware release from the tagged
source; binaries are never committed.

| Folder | What |
|---|---|
| [`module/`](module/) | Module board firmware (STM32G031, RS-485 slave) + the RS-485 bridge build |
| [`shared/`](shared/) | Code both ends compile in: [`sfbus.h`](shared/sfbus.h), the RS-485 bus protocol |

Nothing released yet.

**CI** ([`firmware.yml`](../.github/workflows/firmware.yml)) runs on every PR, for each PlatformIO project
here: `pio test -e native` if the project has an `[env:native]`, then `pio run`. A project with a native
env must set `default_envs` to its board envs, so plain `pio run` doesn't try to build the tests.
