// sfctl: the controller library. Drives split-flap modules over the RS-485 bus (sfbus): requests and
// replies, which modules are present, each module's settings kept on the ESP32 and re-sent after it
// resets, calibration. Every controller build links it: the serial console (src/console.cpp) and,
// later, each application.
//
// The library never prints or reads the console itself: messages go through the log hook and a
// long operation (calibration) checks the abort hook. The defaults print to Serial and never abort.
#pragma once
#include <Arduino.h>
#include "sfbus.h"

namespace sfctl {

const uint8_t  MAX_ADDR = 32;     // module addresses 1..MAX_ADDR
const uint32_t REPLY_MS = 25;     // wait this long for a reply before a retry

struct Pins { int rx, tx, de; };  // de: the transceiver's DE+RE pin (unused with the bridge board)

// Pins and UART for this chip: ESP32 UART2 on GPIO16/17, S3/C3 UART1 on GPIO5/6; DE+RE on GPIO4.
Pins defaultPins();
HardwareSerial &defaultBus();

// Starts the bus and loads the saved settings from flash.
void begin(HardwareSerial &bus = defaultBus(), Pins pins = defaultPins());

using LogFn = void (*)(const char *fmt, ...);
using AbortFn = bool (*)();
void setLog(LogFn fn);
void setAbort(AbortFn fn);

// ---- bus
// Addressed request, retried (tries - 1) times. A broadcast is sent once and returns true, no reply.
bool request(uint8_t addr, uint8_t cmd, sfbus::Frame &out, const void *p = nullptr, uint8_t n = 0, int tries = 2);
uint32_t timeouts();              // requests that got no reply
void clearTimeouts();

// ---- modules
bool known(uint8_t addr);         // answered since the last scan
void setKnown(uint8_t addr, bool k);
bool ping(uint8_t addr, sfbus::Ping &p, int tries = 2);
// Pings 1..maxAddr (at most MAX_ADDR); calls found() for each module that answers, then re-sends its saved settings if it
// has reset. Returns how many answered.
int scan(int maxAddr, void (*found)(uint8_t addr, const sfbus::Ping &p) = nullptr);
// Status (or any command answered by a Status). A module reporting F_FRESH has reset to its compiled
// defaults: its saved settings are pushed back and the status re-read.
bool getStatus(uint8_t addr, sfbus::Status &s, uint8_t cmd = sfbus::C_STATUS, const void *p = nullptr, uint8_t n = 0);
bool getCfg(uint8_t addr, int32_t *out);          // out[sfbus::K_COUNT]
bool setKey(uint8_t addr, uint8_t key, int32_t value);

// ---- settings kept on the ESP32 (flash), one set per address
bool hasSaved(uint8_t addr);
bool storeSettings(uint8_t addr, const int32_t *v);   // false if the flash write failed
bool autoSave(uint8_t addr);      // read the module's settings and store them
bool forget(uint8_t addr);         // false if the flash delete failed
bool restoreIfReset(uint8_t addr);   // broadcast = every known module; false while a push is still pending

// ---- procedures
// Polls until the module is idle. The abort hook stops every module and returns false.
bool waitIdle(uint8_t addr, sfbus::Status &s, uint32_t maxMs);
// Homes revs + 1 times (revs 1..32); each hall-to-hall rev measures counts/rev. Sets cpr and rescales the
// settings kept in counts, then stores them.
void calibrate(uint8_t addr, int revs);
// "The drum shows flap n now": shifts foff so this position is flap n, then stores the settings.
void markHere(uint8_t addr, int n);

}  // namespace sfctl
