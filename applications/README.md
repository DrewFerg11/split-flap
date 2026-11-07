# applications/

Displays built from the shared hardware, PCBs and firmware, one folder per application
(first: `premier-league-table/`). An application holds its own controller build, configuration
and flap sets; it uses the shared parts rather than copying them.

**Releases:** tagged `app/<application>/vX.Y.Z`. CI builds the firmware from the tagged
source, and each release lists the exact `pcb/`, `hw/` and `fw/` versions it was tested with.

Nothing migrated or released yet.
