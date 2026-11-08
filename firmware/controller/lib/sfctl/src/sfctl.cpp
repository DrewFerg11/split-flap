#include "sfctl.h"
#include <Preferences.h>
#include <stdarg.h>
#include "calib.h"

using namespace sfbus;

namespace sfctl {

// Flash namespace for the stored settings. "ltmhost" is the name the bench controller used before
// the migration; keeping it keeps every module's stored settings across the update.
static const char *NVS_NS = "ltmhost";

static HardwareSerial *Bus = nullptr;
static Pins           pins;
static Parser         parser;
static Preferences    prefs;
static bool           knownAddr[MAX_ADDR + 1];
static int32_t        saved[MAX_ADDR + 1][K_COUNT];
static bool           savedValid[MAX_ADDR + 1];
static bool           pushPending[MAX_ADDR + 1];   // reset seen, stored settings not fully pushed yet
static uint32_t       timeoutCount = 0;

static void serialLog(const char *fmt, ...) {
  char buf[256];
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(buf, sizeof buf, fmt, ap);
  va_end(ap);
  Serial.print(buf);
}
static bool neverAbort() { return false; }
static LogFn   say = serialLog;
static AbortFn shouldAbort = neverAbort;

void setLog(LogFn fn) { say = fn ? fn : serialLog; }
void setAbort(AbortFn fn) { shouldAbort = fn ? fn : neverAbort; }

Pins defaultPins() {
#if CONFIG_IDF_TARGET_ESP32
  return {16, 17, 4};
#else                                          // S3 / C3: the C3 has no UART2; UART0 is left alone
  return {5, 6, 4};
#endif
}

HardwareSerial &defaultBus() {
#if CONFIG_IDF_TARGET_ESP32
  return Serial2;
#else
  return Serial1;
#endif
}

static void key(char *k, size_t n, unsigned addr) { snprintf(k, n, "n%u", addr); }

static void loadSaved() {
  prefs.begin(NVS_NS, true);
  for (int a = 1; a <= MAX_ADDR; a++) {
    char k[8]; key(k, sizeof k, a);
    savedValid[a] = prefs.getBytesLength(k) == sizeof saved[a] && prefs.getBytes(k, saved[a], sizeof saved[a]) == sizeof saved[a];
  }
  prefs.end();
}

void begin(HardwareSerial &bus, Pins p) {
  Bus = &bus;
  pins = p;
  pinMode(pins.de, OUTPUT);
  digitalWrite(pins.de, LOW);
  Bus->begin(BAUD, SERIAL_8N1, pins.rx, pins.tx);
  delay(300);
  loadSaved();
}

// ---------------------------------------------------------------- bus ---

static void sendFrame(uint8_t addr, uint8_t cmd, const void *p, uint8_t n) {
  uint8_t buf[MAX_FRAME];
  size_t len = encode(buf, addr, cmd, p, n);
  while (Bus->available()) Bus->read();        // drop stale bytes
  digitalWrite(pins.de, HIGH);
  Bus->write(buf, len);
  Bus->flush();                                // returns after the last bit
  digitalWrite(pins.de, LOW);
}

static bool waitReply(uint8_t addr, uint8_t cmd, Frame &out) {
  uint32_t t0 = millis();
  while (millis() - t0 < REPLY_MS) {
    while (Bus->available()) {
      if (parser.feed(Bus->read(), millis())) {
        const Frame &f = parser.frame();
        if (f.addr == addr && f.cmd == (cmd | REPLY)) { out = f; return true; }
      }
    }
    delayMicroseconds(100);
  }
  return false;
}

bool request(uint8_t addr, uint8_t cmd, Frame &out, const void *p, uint8_t n, int tries) {
  if (addr == ADDR_BCAST) { sendFrame(addr, cmd, p, n); return true; }
  for (int i = 0; i < tries; i++) {
    sendFrame(addr, cmd, p, n);
    if (waitReply(addr, cmd, out)) return true;
    timeoutCount++;
  }
  return false;
}

uint32_t timeouts() { return timeoutCount; }
void clearTimeouts() { timeoutCount = 0; }

// ------------------------------------------------------------ modules ---

// One module's address (not broadcast): everything indexed per address checks this first.
static bool inRange(uint8_t addr) { return addr >= 1 && addr <= MAX_ADDR; }

bool known(uint8_t addr) { return inRange(addr) && knownAddr[addr]; }
void setKnown(uint8_t addr, bool k) { if (inRange(addr)) knownAddr[addr] = k; }

bool hasSaved(uint8_t addr) { return inRange(addr) && savedValid[addr]; }

// The module clears F_FRESH on the first SET it accepts, so F_FRESH can't tell whether a push finished:
// pushPending stays set until every key has gone through, and getStatus() retries until it has.
static bool pushSaved(uint8_t addr) {
  if (!savedValid[addr]) { pushPending[addr] = false; return true; }
  pushPending[addr] = true;
  Frame f;
  for (int k = 0; k < K_COUNT; k++) {
    SetMsg m = { (uint8_t)k, saved[addr][k] };
    if (!request(addr, C_SET, f, &m, sizeof m)) { say("[%u] settings push failed, will retry\n", addr); return false; }
  }
  pushPending[addr] = false;
  say("[%u] module had reset: pushed its saved settings\n", addr);
  return true;
}

bool getStatus(uint8_t addr, Status &s, uint8_t cmd, const void *p, uint8_t n) {
  if (!inRange(addr)) return false;
  Frame f;
  if (!request(addr, cmd, f, p, n) || f.len < sizeof(Status)) return false;
  memcpy(&s, f.data, sizeof s);
  knownAddr[addr] = true;
  if (((s.flags & F_FRESH) || pushPending[addr]) && savedValid[addr]) {
    pushSaved(addr);
    Frame g;
    if (request(addr, C_STATUS, g) && g.len >= sizeof s) memcpy(&s, g.data, sizeof s);
  }
  return true;
}

bool getCfg(uint8_t addr, int32_t *out) {
  if (!inRange(addr)) return false;
  Frame f;
  if (!request(addr, C_GET, f) || f.len < sizeof(int32_t) * K_COUNT) return false;
  memcpy(out, f.data, sizeof(int32_t) * K_COUNT);
  return true;
}

bool setKey(uint8_t addr, uint8_t key, int32_t value) {
  SetMsg m = { key, value };
  Frame f;
  return request(addr, C_SET, f, &m, sizeof m);
}

bool ping(uint8_t addr, Ping &p, int tries) {
  if (!inRange(addr)) return false;
  Frame f;
  if (!request(addr, C_PING, f, nullptr, 0, tries) || f.len < sizeof(Ping)) return false;
  memcpy(&p, f.data, sizeof p);
  knownAddr[addr] = true;
  return true;
}

int scan(int maxAddr, void (*found)(uint8_t addr, const Ping &p)) {
  int count = 0;
  for (int a = 1; a <= maxAddr; a++) {
    knownAddr[a] = false;
    Ping p;
    if (ping(a, p, 1)) {
      count++;
      if (found) found(a, p);
      restoreIfReset(a);                       // a module that just powered up gets its settings back now
    }
  }
  timeoutCount = 0;
  return count;
}

// ------------------------------------------------------------ settings ---

void storeSettings(uint8_t addr, const int32_t *v) {
  if (!inRange(addr)) return;
  char k[8]; key(k, sizeof k, addr);
  prefs.begin(NVS_NS, false); prefs.putBytes(k, v, sizeof(int32_t) * K_COUNT); prefs.end();
  memcpy(saved[addr], v, sizeof(int32_t) * K_COUNT); savedValid[addr] = true;
}

// Every setting change is kept on the ESP32 straight away, so there is no separate 'save' to forget.
bool autoSave(uint8_t addr) {
  int32_t v[K_COUNT];
  if (!getCfg(addr, v)) return false;
  storeSettings(addr, v);
  return true;
}

void forget(uint8_t addr) {
  if (!inRange(addr)) return;
  char k[8]; key(k, sizeof k, addr);
  prefs.begin(NVS_NS, false); prefs.remove(k); prefs.end();
  savedValid[addr] = false;
  pushPending[addr] = false;
}

// A module that has reset still runs the compiled defaults. Reading its status makes getStatus() push its
// saved settings back, so do this before the first real command to it.
void restoreIfReset(uint8_t addr) {
  Status s;
  if (addr != ADDR_BCAST) { getStatus(addr, s); return; }
  for (int a = 1; a <= MAX_ADDR; a++) if (knownAddr[a]) getStatus(a, s);
}

// --------------------------------------------------------- procedures ---

bool waitIdle(uint8_t addr, Status &s, uint32_t maxMs) {
  uint32_t t0 = millis();
  while (millis() - t0 < maxMs) {
    if (shouldAbort()) { Frame f; request(ADDR_BCAST, C_STOP, f); say("stopped\n"); return false; }
    delay(60);
    if (getStatus(addr, s) && s.mode == M_IDLE) return true;
  }
  say("[%u] timed out\n", addr);
  return false;
}

// Home, then home 'revs' more times; each home is exactly one drum rev between hall edges.
// The hall edge count is the stop count minus how far it ran past the edge (Status.aux).
void calibrate(uint8_t addr, int revs) {
  int32_t v[K_COUNT];
  if (!getCfg(addr, v)) { say("[%u] no reply\n", addr); return; }
  int32_t oldCpr = v[K_CPR];
  // stay at the magnet after each home; a huge cpr so the "no hall edge in 2 revs" guard can't trip
  bool ok = setKey(addr, K_REST, -1) && setKey(addr, K_CPR, 200000);
  if (ok) say("[%u] calibrating: %d drum revs at home duty %ld%% ('x' stops)\n", addr, revs, (long)v[K_HOME]);
  else say("[%u] no reply while preparing\n", addr);

  int32_t edges[33];
  Status s;
  Frame f;
  for (int i = 0; i <= revs && ok; i++) {
    ok = request(addr, C_HOME, f) && waitIdle(addr, s, 60000);
    if (ok && s.stop != R_HOMED) { say("[%u] home failed: %s\n", addr, STOP_NAMES[s.stop]); ok = false; }
    if (!ok) break;
    edges[i] = s.count - s.aux;
    if (i) say("  rev %d: %ld counts\n", i, (long)(edges[i] - edges[i - 1]));
  }
  if (!ok) {
    bool restored = setKey(addr, K_CPR, oldCpr);
    restored = setKey(addr, K_REST, v[K_REST]) && restored;   // both attempted, whatever the first did
    if (restored) say("[%u] calibration abandoned, settings restored\n", addr);
    else say("[%u] calibration abandoned; restoring cpr/rest failed: check 'cfg' (cpr should be %ld)\n", addr, (long)oldCpr);
    return;
  }

  int32_t cpr = calib::cprFromEdges(edges, revs);
  int32_t spread = calib::revSpread(edges, revs, cpr);
  // The slow zone, decel zone and brake lead were tuned in counts for 10856/rev: keep them the same share of a flap.
  int32_t zone = calib::rescale(v[K_ZONE], cpr, oldCpr), dzone = calib::rescale(v[K_DZONE], cpr, oldCpr);
  int32_t lead = calib::rescale(v[K_LEAD], cpr, oldCpr), foff = calib::rescale(v[K_FOFF], cpr, oldCpr);
  // Every write is attempted (rest must leave its temporary -1 even if another key failed). Only a
  // complete set is stored; after a partial one the previous stored settings stay, so the module gets
  // them back on its next reset.
  const struct { uint8_t key; int32_t value; } w[] = {
    {K_CPR, cpr}, {K_ZONE, zone}, {K_DZONE, dzone}, {K_LEAD, lead}, {K_FOFF, foff}, {K_REST, v[K_REST]} };
  bool written = true;
  for (const auto &kv : w) written = setKey(addr, kv.key, kv.value) && written;
  if (!written) {
    say("[%u] measured cpr %ld, but not every setting reached the module; nothing stored. Check 'cfg' and run cal again\n",
        addr, (long)cpr);
    return;
  }
  autoSave(addr);
  say("[%u] cpr %ld counts/rev (was %ld; revs agree within %ld counts) = %.1f counts/flap\n",
       addr, (long)cpr, (long)oldCpr, (long)spread, (float)cpr / v[K_FLAPS]);
  say("[%u] scaled zone %ld, dzone %ld, lead %ld, foff %ld. Next: f 0, nudge with 'go <counts>', then 'here 0'. 'save' when done\n",
       addr, (long)zone, (long)dzone, (long)lead, (long)foff);
}

void markHere(uint8_t addr, int n) {
  int32_t v[K_COUNT];
  Status s;
  if (!getCfg(addr, v) || !getStatus(addr, s)) { say("[%u] no reply\n", addr); return; }
  if (!(s.flags & F_HOMED)) { say("[%u] not homed, run home first\n", addr); return; }
  int32_t foff = calib::foffForHere(v[K_FOFF], s.flapX100 / 100.0f, n, v[K_FLAPS], v[K_CPR]);
  if (!setKey(addr, K_FOFF, foff)) { say("[%u] no reply, foff unchanged\n", addr); return; }
  autoSave(addr);
  say("[%u] was reading flap %.2f; foff %ld -> %ld, so this is now flap %d (saved)\n",
       addr, s.flapX100 / 100.0f, (long)v[K_FOFF], (long)foff, n);
}

}  // namespace sfctl
