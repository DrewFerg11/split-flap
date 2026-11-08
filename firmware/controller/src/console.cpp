// Split-flap controller: the default build, a serial console for driving modules on the bench.
// The module handling is lib/sfctl; this file is the console on top of it (commands, printing,
// follow / watch / cycle).
//
// Targets: ESP32-WROOM DevKit V1 (env esp32dev), ESP32-S3 (env s3), ESP32-C3 (env c3).
//   USB serial 115200, type ? for commands. 250 kbps bus (sfbus.h).
//   ESP32: UART2 RX GPIO16, TX GPIO17, DE+RE GPIO4.  S3 / C3: UART1 RX GPIO5, TX GPIO6, DE+RE GPIO4.
//   DE is unused with the bridge board.
//
// Commands go to the selected module (default 1), or prefix an address: "2 home", "* f 5" (* = all,
// no replies). Motion commands are followed until the module stops, then the result is printed.
// Settings live on the ESP32 and are pushed back automatically whenever that module reports a reset.
#include <Arduino.h>
#include "console_parse.h"
#include "sfctl.h"

using namespace sfbus;
using sfctl::MAX_ADDR;

static const uint32_t FOLLOW_POLL_MS = 60, FOLLOW_MAX_MS = 30000;

static uint8_t  cur = 1;                       // selected module
static bool     following[MAX_ADDR + 1];
static uint32_t followStart = 0, lastFollowPoll = 0;
static uint32_t watchMs = 0, lastWatch = 0;
static uint8_t  cycleAddr = 0;
static int      cycleLeft = 0, cycleFlaps = 52, cycleNext = 0;
static uint32_t cycleAt = 0;
static bool     cycleFailed = false;           // cycleAddr == ADDR_BCAST: some module stopped short

// ------------------------------------------------------------ printing ---

static void printStatus(uint8_t addr, const Status &s) {
  char flap[24];
  if (s.flags & F_HOMED) snprintf(flap, sizeof flap, "flap %5.2f", s.flapX100 / 100.0f);
  else                   snprintf(flap, sizeof flap, "not homed ");
  Serial.printf("[%u] %-6s %s  count %7ld  duty %4d%%  I %4u mA (peak %u)  hall %s  enum %d%s\n",
                addr, s.mode < 6 ? MODE_NAMES[s.mode] : "?", flap, (long)s.count, s.duty, s.mA, s.peakmA,
                (s.flags & F_HALL) ? "MAGNET" : "-", (s.flags & F_ENUM) ? 1 : 0,
                (s.flags & F_FRESH) ? "  [default settings]" : "");
}

static void printResult(uint8_t addr, const Status &s) {
  const char *why = s.stop < sizeof(STOP_NAMES) / sizeof(STOP_NAMES[0]) ? STOP_NAMES[s.stop] : "?";
  switch (s.stop) {
    case R_DONE:
      if (s.target != 255) Serial.printf("[%u] at flap %d: showing %.2f, error %+d counts, lead now %d, peak %u mA\n",
                                         addr, s.target, s.flapX100 / 100.0f, s.lastErr, s.lead, s.peakmA);
      else Serial.printf("[%u] move done: error %+d counts, lead now %d, peak %u mA\n", addr, s.lastErr, s.lead, s.peakmA);
      break;
    case R_HOMED:
      Serial.printf("[%u] homed: stopped %+d counts past the hall edge, showing flap %.2f\n", addr, s.aux,
                    s.flapX100 / 100.0f);
      break;
    case T_PASS: case T_NOCOUNTS: case T_FEW: case T_SAMESIGN: case T_BACKWARDS:
      Serial.printf("[%u] %s  (forward %+d, reverse %+d counts)\n", addr, why, s.lastErr, s.aux);
      break;
    default:
      Serial.printf("[%u] stopped: %s\n", addr, why);
      printStatus(addr, s);
  }
}

static void printFound(uint8_t a, const Ping &p) {
  Serial.printf("  [%d] fw %u  uid %08lx-%08lx-%08lx%s\n", a, p.fw, (unsigned long)p.uid[0],
                (unsigned long)p.uid[1], (unsigned long)p.uid[2], sfctl::hasSaved(a) ? "  (saved settings here)" : "");
}

// ------------------------------------------------------------- actions ---

static void follow(uint8_t addr) {
  if (addr == ADDR_BCAST) { for (int a = 1; a <= MAX_ADDR; a++) following[a] = sfctl::known(a); }
  else following[addr] = true;
  followStart = lastFollowPoll = millis();
}

static bool cycleBusy() {                      // a move for the current cycle is still running
  if (cycleAddr != ADDR_BCAST) return following[cycleAddr];
  for (int a = 1; a <= MAX_ADDR; a++) if (following[a]) return true;
  return false;
}

static void scan(int maxAddr) {
  Serial.printf("scanning 1..%d\n", maxAddr);
  int found = sfctl::scan(maxAddr, printFound);
  Serial.printf("%d module%s found%s\n", found, found == 1 ? "" : "s",
                found ? "" : ". Check: 12 V on, A/B not swapped, ESP TX->RX crossed, bridge/adapter powered");
}

static void printHelp() {
  Serial.print(
    "\nSplit-flap controller - modules over RS-485\n"
    "  [addr] <command>   addr = 1..32 or * (all, no replies). No addr = the selected module.\n"
    "  a; b; c         several commands at once, e.g.  3 f 1; 1 f 2\n"
    "  ?               this list\n"
    "  scan [n]        find modules 1..n (default 8)\n"
    "  use <addr>      select a module\n"
    "  x               STOP ALL (broadcast)\n"
    "  s               status            ping   firmware + unique ID\n"
    "  w [ms]          watch status every ms (default 200; w 0 = off)\n"
    "  test            self-test: short pulses fwd/back, checks encoder\n"
    "  home            run forward to the hall edge\n"
    "  f <n>           go to flap n (forward only, needs home)\n"
    "  cycle [n]       step n flaps one at a time, 1 s apart (x stops). * cycle = all modules together\n"
    "  d <pct>         drive open loop -100..100 (d 0 = stop). Stall guard + 10 s limit\n"
    "  go <counts>     forward by a count     rev [n]  forward n drum revs\n"
    "  z               zero the count (forgets home)\n"
    "  cal [revs]      measure counts/rev from hall edges (default 3 revs), set cpr\n"
    "  here [n]        the drum shows flap n now (default 0): sets foff\n"
    "  id              blink the module's LED fast for 3 s\n"
    "  set <key> <v>   change a setting on the module (cfg lists keys)\n"
    "  cfg             show the module's settings\n"
    "  save            store the module's settings here now. set / here / cal already do this; also keeps the learned lead\n"
    "  forget          delete the stored settings for this address\n\n");
}

static void handle(const std::string &raw) {
  console::Parsed p;
  if (!console::parseLine(raw, cur, ADDR_BCAST, MAX_ADDR, p)) return;
  uint8_t addr = p.addr;
  const std::string &cmd = p.cmd, &rest = p.rest;
  bool hasArg = p.hasArg, explicitAddr = p.explicitAddr;
  long arg = p.arg;
  bool bcast = addr == ADDR_BCAST;
  Status s;
  Frame f;

  if (cmd == "?" || cmd == "help") { printHelp(); return; }
  if (cmd == "scan") { scan(hasArg ? constrain(arg, 1, MAX_ADDR) : 8); return; }
  if (cmd == "use")  { if (hasArg) cur = constrain(arg, 1, MAX_ADDR); Serial.printf("selected module %u\n", cur); return; }
  if (cmd == "x" && !explicitAddr) addr = ADDR_BCAST, bcast = true;
  if (cmd == "w")    { watchMs = hasArg ? arg : (watchMs ? 0 : 200); if (!bcast) cur = addr; Serial.printf("watch %s\n", watchMs ? "on" : "off"); return; }

  if (cmd == "s") {
    if (bcast) { for (int a = 1; a <= MAX_ADDR; a++) if (sfctl::known(a) && sfctl::getStatus(a, s)) printStatus(a, s); return; }
    if (sfctl::getStatus(addr, s)) { printStatus(addr, s); if (s.stop != R_NONE) printResult(addr, s); }
    else Serial.printf("[%u] no reply\n", addr);
    return;
  }
  if (cmd == "ping") {
    if (bcast) { Serial.println("ping needs an address"); return; }
    Ping pg;
    if (sfctl::ping(addr, pg))
      Serial.printf("[%u] fw %u  uid %08lx-%08lx-%08lx\n", addr, pg.fw, (unsigned long)pg.uid[0], (unsigned long)pg.uid[1], (unsigned long)pg.uid[2]);
    else Serial.printf("[%u] no reply\n", addr);
    return;
  }

  // a module that has reset gets its saved settings back before the command reaches it
  if (cmd != "x" && cmd != "forget") sfctl::restoreIfReset(addr);

  if (cmd == "cal" || cmd == "here") {
    if (bcast) { Serial.println("needs one module"); return; }
    if (cmd == "cal") sfctl::calibrate(addr, hasArg ? constrain(arg, 1, 32) : 3);
    else sfctl::markHere(addr, hasArg ? arg : 0);
    return;
  }

  // commands that answer with a status, some of which start motion
  uint8_t c = 0, payload[8]; uint8_t n = 0; bool motion = false;
  if      (cmd == "x")    c = C_STOP;
  else if (cmd == "home") { c = C_HOME; motion = true; }
  else if (cmd == "test") { c = C_TEST; motion = true; }
  else if (cmd == "z")    c = C_ZERO;
  else if (cmd == "id")   c = C_IDENT;
  else if (cmd == "f")    { if (!hasArg) { Serial.println("usage: f <flap>"); return; } c = C_FLAP; payload[0] = (uint8_t)arg; n = 1; motion = true; }
  else if (cmd == "d")    { if (!hasArg) { Serial.println("usage: d <pct>"); return; } c = C_DRIVE; payload[0] = (uint8_t)(int8_t)constrain(arg, -100, 100); n = 1; motion = arg != 0; }
  else if (cmd == "go")   { int32_t v = arg; c = C_MOVE; memcpy(payload, &v, 4); n = 4; motion = true; }
  else if (cmd == "rev")  { int16_t v = hasArg ? arg : 1; c = C_REV; memcpy(payload, &v, 2); n = 2; motion = true; }
  else if (cmd == "set") {
    size_t sp2 = rest.find(' ');
    std::string key = sp2 == std::string::npos ? rest : rest.substr(0, sp2);
    int k = -1;
    for (int i = 0; i < K_COUNT; i++) if (key == KEY_NAMES[i]) k = i;
    if (k < 0 || sp2 == std::string::npos) { Serial.println("usage: set <key> <value>   (cfg lists the keys)"); return; }
    SetMsg m = { (uint8_t)k, (int32_t)console::toInt(rest.substr(sp2 + 1)) };
    c = C_SET; memcpy(payload, &m, sizeof m); n = sizeof m;
  }
  else if (cmd == "cfg" || cmd == "save") {
    if (bcast) { Serial.println("needs an address"); return; }
    int32_t v[K_COUNT];
    if (!sfctl::getCfg(addr, v)) { Serial.printf("[%u] no reply\n", addr); return; }
    if (cmd == "save") {
      sfctl::storeSettings(addr, v);
      Serial.printf("[%u] settings saved on the ESP32\n", addr);
    }
    for (int i = 0; i < K_COUNT; i++)
      Serial.printf("  %-6s %7ld   %s%s\n", KEY_NAMES[i], (long)v[i], KEY_HELP[i], v[i] != KEY_DEFAULTS[i] ? "  *" : "");
    return;
  }
  else if (cmd == "forget") {
    if (bcast) { Serial.println("needs an address"); return; }
    sfctl::forget(addr);
    Serial.printf("[%u] stored settings deleted (module keeps its current ones until reset)\n", addr);
    return;
  }
  else if (cmd == "cycle") {
    if (bcast) {                               // all known modules step to the same flap together
      int first = 0, count = 0;
      for (int a = 1; a <= MAX_ADDR; a++) {
        if (!sfctl::known(a)) continue;
        if (!sfctl::getStatus(a, s)) { Serial.printf("[%d] no reply\n", a); return; }
        if (!(s.flags & F_HOMED)) { Serial.printf("[%d] not homed, run home first\n", a); return; }
        if (!first) {
          int32_t v[K_COUNT];
          if (!sfctl::getCfg(a, v)) { Serial.printf("[%d] no reply\n", a); return; }
          first = a; cycleFlaps = v[K_FLAPS];
          cycleNext = (lroundf(s.flapX100 / 100.0f) + 1) % cycleFlaps;
        }
        count++;
      }
      if (!count) { Serial.println("no modules known (scan first)"); return; }
      cycleAddr = ADDR_BCAST; cycleFailed = false;
      cycleLeft = hasArg ? arg : cycleFlaps;
      cycleAt = millis();
      Serial.printf("[*] cycling %d modules, %d flaps, 1 s each, from flap %d of module %d (x stops)\n",
                    count, cycleLeft, cycleNext, first);
      return;
    }
    int32_t v[K_COUNT];
    if (!sfctl::getCfg(addr, v) || !sfctl::getStatus(addr, s)) { Serial.printf("[%u] no reply\n", addr); return; }
    if (!(s.flags & F_HOMED)) { Serial.printf("[%u] not homed, run home first\n", addr); return; }
    cycleAddr = addr; cycleFlaps = v[K_FLAPS];
    cycleLeft = hasArg ? arg : cycleFlaps;
    cycleNext = (lroundf(s.flapX100 / 100.0f) + 1) % cycleFlaps;
    cycleAt = millis();
    Serial.printf("[%u] cycling %d flaps, 1 s each (x stops)\n", addr, cycleLeft);
    return;
  }
  else { Serial.printf("unknown command '%s' (? for help)\n", cmd.c_str()); return; }

  if (cmd == "x") cycleLeft = 0;
  if (bcast) {
    sfctl::request(addr, c, f, payload, n);
    Serial.printf("[*] sent %s\n", cmd.c_str());
    if (c == C_SET) for (int a = 1; a <= MAX_ADDR; a++) if (sfctl::known(a)) sfctl::autoSave(a);
    if (motion) follow(addr);
    return;
  }
  if (!sfctl::getStatus(addr, s, c, payload, n)) { Serial.printf("[%u] no reply\n", addr); return; }
  if (c == C_FLAP && s.stop == R_NOTHOMED) { printResult(addr, s); return; }
  if (motion) follow(addr);
  else if (c == C_SET || c == C_STOP || c == C_ZERO || c == C_IDENT) printStatus(addr, s);
  if (c == C_SET && sfctl::autoSave(addr)) Serial.printf("[%u] saved\n", addr);
}

// 'x' typed during a long operation (calibration) stops it.
static bool xTyped() { return Serial.available() && tolower(Serial.read()) == 'x'; }

// ---------------------------------------------------------------- main ---

void setup() {
  Serial.begin(115200);
#if ARDUINO_USB_CDC_ON_BOOT
  while (!Serial && millis() < 3000) delay(10);  // native USB: give the monitor time to attach
#endif
  sfctl::setAbort(xTyped);
  sfctl::begin();
  Serial.println("\n=== Split-flap controller (modules over RS-485) ===  ? for commands");
  scan(8);
  for (int a = 1; a <= MAX_ADDR; a++) if (sfctl::known(a)) { cur = a; break; }
  Serial.printf("selected module %u\n", cur);
}

void loop() {
  static std::string lineBuf;
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\r' || ch == '\n') {            // "3 f 1; 1 f 2" runs both, a few ms apart
      std::string l = lineBuf; lineBuf.clear();
      for (const auto &part : console::splitCommands(l)) handle(part);
    }
    else if (ch == 0x08 || ch == 0x7f) { if (!lineBuf.empty()) lineBuf.pop_back(); }
    else if (ch >= 0x20 && ch < 0x7f && lineBuf.size() < 80) lineBuf += ch;
  }

  uint32_t now = millis();
  Status s;

  // follow motion until each module is idle again
  if (now - lastFollowPoll >= FOLLOW_POLL_MS) {
    lastFollowPoll = now;
    for (int a = 1; a <= MAX_ADDR; a++) {
      if (!following[a]) continue;
      if (now - followStart > FOLLOW_MAX_MS) { following[a] = false; Serial.printf("[%d] still moving after 30 s, stopped following\n", a); cycleFailed = true; continue; }
      if (!sfctl::getStatus(a, s)) continue;
      if (s.mode == M_IDLE) {
        following[a] = false;
        printResult(a, s);
        if (a == cycleAddr && cycleLeft > 0) {
          if (s.stop == R_DONE && --cycleLeft > 0) cycleAt = now + 1000;
          else cycleLeft = 0;
        }
        if (cycleAddr == ADDR_BCAST && cycleLeft > 0 && s.stop != R_DONE) cycleFailed = true;
      }
    }
    // cycle all: the step is over once every module has stopped
    if (cycleAddr == ADDR_BCAST && cycleLeft > 0 && !cycleBusy() && (int32_t)(cycleAt - now) > 50000) {   // 100 s sentinel = move in flight
      if (cycleFailed) { Serial.println("[*] a module stopped short, cycle stopped"); cycleLeft = 0; }
      else if (--cycleLeft > 0) cycleAt = now + 1000;
    }
  }

  // cycle: next flap once the last move has finished
  if (cycleLeft > 0 && !cycleBusy() && (int32_t)(now - cycleAt) >= 0) {
    uint8_t flap = cycleNext;
    cycleNext = (cycleNext + 1) % cycleFlaps;
    if (cycleAddr == ADDR_BCAST) { Frame f; sfctl::request(ADDR_BCAST, C_FLAP, f, &flap, 1); follow(ADDR_BCAST); }
    else if (sfctl::getStatus(cycleAddr, s, C_FLAP, &flap, 1)) follow(cycleAddr);
    else { Serial.printf("[%u] no reply, cycle stopped\n", cycleAddr); cycleLeft = 0; }
    cycleAt = now + 100000;                    // re-armed when the move finishes
  }

  if (watchMs && now - lastWatch >= watchMs) {
    lastWatch = now;
    if (sfctl::getStatus(cur, s)) printStatus(cur, s);
    else Serial.printf("[%u] no reply\n", cur);
  }
}
