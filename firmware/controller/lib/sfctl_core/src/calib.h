// Calibration maths for the controller: hardware-free, so the native unit tests can run it.
// sfctl::calibrate() and sfctl::markHere() (lib/sfctl) feed these from the module's replies.
#pragma once
#include <math.h>
#include <stdint.h>

namespace sfctl {
namespace calib {

// Counts per drum revolution from hall-edge counts edges[0..revs] (one home per revolution).
inline int32_t cprFromEdges(const int32_t *edges, int revs) {
  return lroundf((float)(edges[revs] - edges[0]) / revs);
}

// Largest difference between any one revolution and the average: how well the revs agree.
inline int32_t revSpread(const int32_t *edges, int revs, int32_t cpr) {
  int32_t spread = 0;
  for (int i = 1; i <= revs; i++) {
    int32_t d = edges[i] - edges[i - 1] - cpr;
    if (d < 0) d = -d;
    if (d > spread) spread = d;
  }
  return spread;
}

// A setting in counts (slow zone, decel zone, brake lead, flap offset) rescaled to a new cpr, so it
// stays the same share of a flap.
inline int32_t rescale(int32_t counts, int32_t newCpr, int32_t oldCpr) {
  float k = (float)newCpr / oldCpr;
  return lroundf(counts * k);
}

// "The drum shows flap n now": the flap offset that makes the current position flap n's position.
// flapNow is the module's reading (Status.flapX100 / 100). Shifts by the shortest way round.
inline int32_t foffForHere(int32_t foff, float flapNow, int n, int32_t flaps, int32_t cpr) {
  float f = flaps, d = flapNow - n;
  d = fmodf(d, f);
  if (d > f / 2) d -= f;
  if (d < -f / 2) d += f;
  return foff + lroundf(d * cpr / f);
}

}  // namespace calib
}  // namespace sfctl
