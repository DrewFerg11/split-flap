// Motion maths for the module: hardware-free, so the native unit tests can run it on the PC.
// node.cpp feeds these from its settings (cfg[]), the encoder and millis().
// Counts are + forward (flaps falling). Arduino's min/abs/constrain macros are avoided on purpose.
#pragma once
#include <math.h>
#include <stdint.h>
#include "sfbus.h"

namespace motion {

inline float countsPerFlap(int32_t cpr, int32_t flaps) { return (float)cpr / flaps; }

// Encoder counts come from the free-running 32-bit TIM2 and wrap past INT32_MAX in long service.
// Positions are compared only through these: modular 32-bit arithmetic, well defined (no signed
// overflow) and exact across the wrap while the two positions are less than 2^31 counts apart.
inline int32_t countDiff(int32_t a, int32_t b) { return (int32_t)((uint32_t)a - (uint32_t)b); }   // a - b
inline int32_t countAdd(int32_t a, int64_t d) { return (int32_t)((uint32_t)a + (uint32_t)d); }    // a + d

// Flap number folded into 0..flaps-1 (so -1 is the last flap).
inline int wrapFlap(int flap, int flaps) { return ((flap % flaps) + flaps) % flaps; }

// Next forward encoder position that shows `flap`: past now + lead (where a brake started now
// would stop), and no more than one revolution beyond it. Closed form in 64 bits, so a small cpr or
// a long time since homing costs nothing (it used to step one revolution per loop pass).
inline int32_t flapTarget(int32_t hallZero, int32_t foff, int32_t cpr, int32_t flaps, int32_t lead,
                          int flap, int32_t now) {
  int32_t base = countAdd(countAdd(hallZero, foff), lroundf(flap * countsPerFlap(cpr, flaps)));
  int64_t d = (int64_t)countDiff(now, base) + lead;       // smallest k with base + k*cpr > now + lead
  int64_t k = (d >= 0 ? d / cpr : -((-d + cpr - 1) / cpr)) + 1;
  return countAdd(base, k * cpr);
}

// Flap showing at encoder count `count`, 0 <= result < flaps (fractional between flaps).
inline float currentFlap(int32_t count, int32_t hallZero, int32_t foff, int32_t cpr, int32_t flaps) {
  float f = fmodf(countDiff(countDiff(count, hallZero), foff) / countsPerFlap(cpr, flaps), flaps);
  return f < 0 ? f + flaps : f;
}

// Start-up ramp: slow -> top over `ramp` ms (t = ms since the motion started).
inline int rampUpDuty(int top, int slow, int ramp, uint32_t t) {
  if (ramp <= 0 || top <= slow || t >= (uint32_t)ramp) return top;
  return slow + (top - slow) * (int)t / ramp;
}

// Duty for a move with `remaining` counts to go: the ramped duty, slowing linearly from fast to slow
// over `dzone` counts before the `zone`-count slow zone.
inline int moveDuty(int rampDuty, int32_t remaining, int fast, int slow, int zone, int dzone) {
  if (remaining < zone) return slow;
  if (dzone > 0 && remaining < zone + dzone) {
    int decel = slow + (fast - slow) * (int)(remaining - zone) / dzone;
    return rampDuty < decel ? rampDuty : decel;
  }
  return rampDuty;
}

// Self-test verdict from the forward and reverse count changes (30 % each way, 250 ms).
inline uint8_t testVerdict(int32_t fwd, int32_t back) {
  int32_t af = fwd < 0 ? -fwd : fwd, ab = back < 0 ? -back : back;
  if (fwd == 0 && back == 0) return sfbus::T_NOCOUNTS;
  if (af < 20 || ab < 20)    return sfbus::T_FEW;
  if (fwd < 0 && back > 0)   return sfbus::T_BACKWARDS;
  if (fwd > 0 && back < 0)   return sfbus::T_PASS;
  return sfbus::T_SAMESIGN;
}

// Brake lead after a move that stopped `err` counts past (+) or short of (-) its target:
// half the error, rounded away from zero, kept in 0..600. Errors within 2 counts leave it alone.
inline int32_t learnLead(int32_t lead, int32_t err) {
  if (err >= -2 && err <= 2) return lead;
  int32_t next = lead + (err + (err > 0 ? 1 : -1)) / 2;
  return next < 0 ? 0 : next > 600 ? 600 : next;
}

}  // namespace motion
