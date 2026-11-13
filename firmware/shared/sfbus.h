// sfbus: the split-flap RS-485 bus protocol, shared by the module firmware (STM32, firmware/module)
// and the controller (ESP32). Both include this one file, so a change here changes both ends.
//
// RS-485, 250 kbps 8N1, half duplex. One frame:
//   0xA5  addr  cmd  len  payload[len]  crc_lo  crc_hi        CRC-16/MODBUS over addr..payload
// Host -> module: addr = module (1..247) or 0xFF broadcast (no reply).
// Module -> host: addr = the module's own address, cmd | 0x80. Modules ignore frames with bit 7 set.
// Every addressed command is answered: C_PING with Ping, C_GET with the settings array, everything else with Status.
#pragma once
#include <stdint.h>
#include <string.h>

namespace sfbus {

const uint8_t  SYNC        = 0xA5;
const uint8_t  ADDR_BCAST  = 0xFF;
const uint8_t  REPLY       = 0x80;
const uint32_t BAUD        = 250000;
const uint8_t  FW_VERSION  = 2;
const uint8_t  MAX_PAYLOAD = 80;
const uint8_t  MAX_FRAME   = MAX_PAYLOAD + 6;
const uint32_t GAP_MS      = 3;       // a gap this long inside a frame drops it

enum Cmd : uint8_t {
  C_PING = 1,   // -> Ping
  C_STATUS,     // -> Status
  C_STOP,       // brake, then coast
  C_HOME,       // run forward to the hall edge
  C_FLAP,       // u8 flap: go forward to that flap (needs home)
  C_DRIVE,      // i8 pct: open loop, -100..100 (0 = stop)
  C_MOVE,       // i32 counts: forward by a count
  C_REV,        // i16 n: forward n drum revolutions
  C_SET,        // SetMsg
  C_GET,        // -> int32 settings[K_COUNT]
  C_ZERO,       // zero the encoder count (forgets home)
  C_TEST,       // motor/encoder self-test, result in Status.stop
  C_IDENT,      // blink the LED fast for 3 s
  C_DISCOVER,   // addr 0, u8 seed: unplaced modules whose ENUM_IN is high answer with Ping, each in its own slot
  C_ASSIGN,     // addr 0, AssignMsg: the module with that UID takes the address and answers Ping from it
  C_UNASSIGN,   // broadcast only: forget the address, drop ENUM_OUT (the host then enumerates again)
  C_ADVANCE,    // broadcast only: every placed module raises ENUM_OUT, so the next module in each row is eligible
};

// Auto-addressing: every module runs the same firmware and powers up unplaced (address 0). The host holds the
// first module's ENUM_IN high; on C_ADVANCE a placed module raises its ENUM_OUT, which is the next one's ENUM_IN.
// So the modules in a row get placed one at a time, in order. Several rows may be eligible at once (one head each):
// they answer a C_DISCOVER in different slots, chosen from their UID and the seed, and the host retries on a clash.
// The host sends C_ADVANCE only once every eligible module is placed, so all rows move one position in step.
const uint8_t  ADDR_NEW    = 0;
const uint8_t  DISCOVER_SLOTS = 8;
const uint32_t SLOT_US     = 2000;   // longer than a Ping reply on the wire (19 bytes = 0.8 ms)

enum Mode : uint8_t { M_IDLE, M_DRIVE, M_HOMING, M_MOVE, M_SETTLE, M_TEST };
static const char *const MODE_NAMES[] = { "idle", "drive", "homing", "move", "settle", "test" };

enum Flag : uint8_t {
  F_HOMED = 1,   // hall zero known
  F_HALL  = 2,   // magnet at the sensor now
  F_FRESH = 4,   // no SET since reset: settings are the compiled defaults
  F_ENUM  = 8,   // ENUM_IN pin is high
};

enum Stop : uint8_t {
  R_NONE, R_DONE, R_HOMED, R_USER, R_STALL, R_NOHALL, R_HALLNOISE, R_OVERCURRENT, R_TIMEOUT, R_NOTHOMED,
  T_PASS, T_NOCOUNTS, T_FEW, T_SAMESIGN, T_BACKWARDS,
};
static const char *const STOP_NAMES[] = {
  "-", "done", "homed", "stopped by command", "STALL (no encoder counts)", "NO HALL EDGE in 2 revs",
  "HALL NOISY", "OVERCURRENT", "drive timeout", "not homed (run home first)",
  "test PASS: motor and encoder agree", "test FAIL: no encoder counts", "test WARN: very few counts (one encoder channel?)",
  "test FAIL: both directions same sign (A/B wiring)", "test FAIL: counts run backwards",
};

// Settings: plain int32 array on the module, indexed by Key. Defaults are the N20 bench values.
enum Key : uint8_t {
  K_CPR, K_FLAPS, K_FAST, K_SLOW, K_HOME, K_RAMP, K_DZONE, K_ZONE, K_LEAD, K_AUTO,
  K_FOFF, K_REST, K_DIR, K_STALL, K_ILIM, K_COUNT
};
static const char *const KEY_NAMES[K_COUNT] = {
  "cpr", "flaps", "fast", "slow", "home", "ramp", "dzone", "zone", "lead", "auto",
  "foff", "rest", "dir", "stall", "ilim",
};
static const char *const KEY_HELP[K_COUNT] = {
  "encoder counts per drum rev", "flaps on the drum", "move duty %", "slow-zone duty %", "homing duty %",
  "ms to ramp slow->fast", "counts to ramp fast->slow", "counts of slow zone before target",
  "brake lead, counts before target", "learn lead from each move (0/1)", "counts from hall edge to flap 0",
  "flap after homing (-1 = none)", "flip motor direction (0/1)", "ms with no counts = stall",
  "jam current, sensed mA = about I x duty (0 = off)",
};
static const int32_t KEY_DEFAULTS[K_COUNT] = {
  10856, 52, 40, 20, 25, 150, 200, 210, 8, 1,
  0, -1, 0, 300, 0,      // dir 0: all v0.1 boards ran backwards with the bench rig's dir 1 (2026-10-29)
};

struct __attribute__((packed)) SetMsg { uint8_t key; int32_t value; };

struct __attribute__((packed)) Ping {
  uint8_t  fw;
  uint32_t uid[3];     // STM32 96-bit unique ID
};

struct __attribute__((packed)) AssignMsg {
  uint32_t uid[3];     // the module being placed (from its Ping)
  uint8_t  addr;       // 1..247
};

// Which reply slot (0..DISCOVER_SLOTS-1) a module takes for a given seed.
inline uint8_t discoverSlot(const uint32_t uid[3], uint8_t seed) {
  uint32_t x = uid[0] ^ (uid[1] * 31u) ^ (uid[2] * 131u) ^ ((uint32_t)seed * 0x9E3779B1u);
  x ^= x >> 15; x *= 0x2C1B3C6Du; x ^= x >> 12;
  return (uint8_t)(x % DISCOVER_SLOTS);
}

struct __attribute__((packed)) Status {
  uint8_t  fw;
  uint8_t  mode;       // Mode
  uint8_t  flags;      // Flag bits
  uint8_t  stop;       // Stop: why the last motion ended / test result
  int32_t  count;      // encoder, + = forward (flaps falling)
  int16_t  flapX100;   // current flap x100, -1 if not homed
  int16_t  lastErr;    // last move: stopped minus target, counts. Test: forward counts
  int16_t  aux;        // test: reverse counts. Home: counts past the hall edge
  int8_t   duty;       // signed %
  uint8_t  target;     // last flap commanded, 255 = none
  uint16_t mA;         // motor current (sense resistor, filtered)
  uint16_t peakmA;     // peak during the last motion
  int16_t  lead;       // brake lead now (auto-learned)
  uint32_t uptimeMs;
};

inline uint16_t crc16(const uint8_t *p, size_t n) {
  uint16_t c = 0xFFFF;
  while (n--) {
    c ^= *p++;
    for (int i = 0; i < 8; i++) c = (c & 1) ? (c >> 1) ^ 0xA001 : c >> 1;
  }
  return c;
}

// Builds a frame into out (>= MAX_FRAME bytes). Returns its length.
inline size_t encode(uint8_t *out, uint8_t addr, uint8_t cmd, const void *payload, uint8_t len) {
  if (len > MAX_PAYLOAD) len = MAX_PAYLOAD;
  out[0] = SYNC; out[1] = addr; out[2] = cmd; out[3] = len;
  if (len) memcpy(out + 4, payload, len);
  uint16_t c = crc16(out + 1, 3 + len);
  out[4 + len] = c & 0xFF;
  out[5 + len] = c >> 8;
  return 6 + len;
}

struct Frame { uint8_t addr, cmd, len; uint8_t data[MAX_PAYLOAD]; };

// Byte-at-a-time receiver. feed() returns true when a complete, CRC-checked frame is in frame().
class Parser {
 public:
  bool feed(uint8_t b, uint32_t nowMs) {
    if (n && nowMs - lastMs > GAP_MS) n = 0;
    lastMs = nowMs;
    if (n == 0 && b != SYNC) return false;
    buf[n++] = b;
    if (n == 4 && buf[3] > MAX_PAYLOAD) { n = 0; return false; }
    if (n >= 4 && n == (size_t)buf[3] + 6) {
      size_t len = n; n = 0;
      uint16_t c = crc16(buf + 1, len - 3);
      if ((c & 0xFF) != buf[len - 2] || (c >> 8) != buf[len - 1]) { crcErrors++; return false; }
      f.addr = buf[1]; f.cmd = buf[2]; f.len = buf[3];
      memcpy(f.data, buf + 4, f.len);
      return true;
    }
    return false;
  }
  const Frame &frame() const { return f; }
  uint32_t crcErrors = 0;

 private:
  uint8_t  buf[MAX_FRAME];
  size_t   n = 0;
  uint32_t lastMs = 0;
  Frame    f;
};

}  // namespace sfbus
