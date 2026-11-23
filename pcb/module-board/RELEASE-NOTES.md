+++
# Notes for this release. The release tag's version must match.
version = "0.1"
status = "Prototype"
status_details = ["ordered 2026-10-19 (10 boards, JLCPCB)", "bring-up in progress"]
prerelease_note = "the first ordered prototype. The silkscreen still reads LEAGUE-TABLE MODULE, and the fab files keep the names they were ordered under."

[bringup]
"Power (12 V in, 3.3 V rail)" = "pass"
"SWD flash" = "pass"
"LED, hall sensor, encoder" = "pass"
"Motor drive" = "pass"
"RS-485 (bridge + board #1, board #2)" = "pass"
"Bus enumeration (ENUM chain)" = "pass"
"Motor current sense (ISEN)" = "pass"
+++

## Summary

One small board per split-flap module: an STM32G031 drives a 12 V N20 encoder motor through a
DRV8870, homes on an A3144 hall sensor, and talks RS-485 to a single ESP32 controller. Boards
chain module to module through right-angle headers on the board edges, and the hall connector
and pinout are the same as on the SplitFlap v5.1 board, so existing sensor leads plug in.

## Known issues

- One of the ten boards received on RS-485 but never transmitted: U2 pin 20 (which drives the transceiver's
  DE) was not soldered to its pad. Reflowed; it works. See DESIGN-1 section 14.
- The bottom-side pin names on J3 (motor) and J5 (hall) are mirrored; count from the square
  pin-1 pad instead. The copper is correct. Fixed in the next revision.
- Silkscreen reads `LEAGUE-TABLE MODULE`; renamed in the next revision.
