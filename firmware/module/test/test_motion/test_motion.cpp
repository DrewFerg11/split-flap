// Motion maths (include/motion.h): flap targets, flap position, duty ramps, self-test verdicts and
// brake-lead learning. The `legacy` functions are the formulas as they were inline in node.cpp
// before the move to motion.h; the equivalence tests pin the new code to them exactly.
#include <stdlib.h>
#include <unity.h>
#include "motion.h"

using namespace sfbus;
using namespace motion;

void setUp() {}
void tearDown() {}

static const int32_t CPR = 10856, FLAPS = 52;

namespace legacy {
static int32_t clamp(int32_t v, int32_t lo, int32_t hi) { return v < lo ? lo : v > hi ? hi : v; }
static int32_t flapTarget(int32_t hallZero, int32_t foff, int32_t cpr, int32_t flaps, int32_t lead, int flap, int32_t now) {
  int32_t base = hallZero + foff + lroundf(flap * ((float)cpr / flaps));
  while (base <= now + lead) base += cpr;
  while (base - cpr > now + lead) base -= cpr;
  return base;
}
static float currentFlap(int32_t count, int32_t hallZero, int32_t foff, int32_t cpr, int32_t flaps) {
  float f = fmodf((count - hallZero - foff) / ((float)cpr / flaps), flaps);
  return f < 0 ? f + flaps : f;
}
static int rampUpDuty(int top, int slow, int ramp, uint32_t t) {
  if (ramp <= 0 || top <= slow || t >= (uint32_t)ramp) return top;
  return slow + (top - slow) * (int)t / ramp;
}
static int moveDuty(int duty, int32_t remaining, int fast, int slow, int zone, int dzone) {
  if (remaining < zone) duty = slow;
  else if (dzone > 0 && remaining < zone + dzone) {
    int d = slow + (fast - slow) * (int)(remaining - zone) / dzone;
    duty = duty < d ? duty : d;
  }
  return duty;
}
static uint8_t testVerdict(int32_t fwd, int32_t back) {
  if (fwd == 0 && back == 0)                  return T_NOCOUNTS;
  if (labs(fwd) < 20 || labs(back) < 20)      return T_FEW;
  if (fwd < 0 && back > 0)                    return T_BACKWARDS;
  if (fwd > 0 && back < 0)                    return T_PASS;
  return T_SAMESIGN;
}
static int32_t learnLead(int32_t lead, int32_t err) {
  if (labs(err) > 2) lead = clamp(lead + (err + (err > 0 ? 1 : -1)) / 2, 0, 600);
  return lead;
}
}  // namespace legacy

// ------------------------------------------------------------ flap maths

static void test_wrap_flap() {
  TEST_ASSERT_EQUAL(0, wrapFlap(0, FLAPS));
  TEST_ASSERT_EQUAL(51, wrapFlap(-1, FLAPS));
  TEST_ASSERT_EQUAL(0, wrapFlap(52, FLAPS));
  TEST_ASSERT_EQUAL(1, wrapFlap(105, FLAPS));
  TEST_ASSERT_EQUAL(0, wrapFlap(7, 1));
}

static void test_flap_target_window() {
  // Always strictly past now + lead, and within one revolution of it.
  const int32_t zeros[] = {0, 1234, -5000};
  const int32_t nows[] = {-30000, -1, 0, 1, 5427, 10855, 10856, 99999};
  for (int32_t hz : zeros)
    for (int32_t now : nows)
      for (int flap = 0; flap < FLAPS; flap++) {
        int32_t lead = 8, tgt = flapTarget(hz, 37, CPR, FLAPS, lead, flap, now);
        TEST_ASSERT_TRUE(tgt > now + lead);
        TEST_ASSERT_TRUE(tgt <= now + lead + CPR);
      }
}

static void test_flap_target_lands_on_flap() {
  for (int flap = 0; flap < FLAPS; flap++) {
    int32_t tgt = flapTarget(500, 37, CPR, FLAPS, 8, flap, 12345);
    TEST_ASSERT_FLOAT_WITHIN(0.01f, (float)flap, currentFlap(tgt, 500, 37, CPR, FLAPS));
  }
}

static void test_flap_target_never_goes_backwards() {
  // Asking for the flap already showing goes a full revolution forward, never back.
  int32_t at = flapTarget(0, 0, CPR, FLAPS, 0, 10, 0);
  TEST_ASSERT_EQUAL(at + CPR, flapTarget(0, 0, CPR, FLAPS, 0, 10, at));
}

static void test_flap_target_extremes() {
  // cpr 1 and far from home: used to loop once per count; now closed form
  TEST_ASSERT_EQUAL(2000000001, flapTarget(0, 0, 1, 1, 0, 0, 2000000000));
  TEST_ASSERT_EQUAL(-1999999999, flapTarget(0, 0, 1, 1, 0, 0, -2000000000));
  // hall zero far behind the count (long run since homing, still < 2^31 counts apart): next flap forward
  int32_t now = 1900000000, tgt = flapTarget(-100000000, 0, CPR, FLAPS, 8, 10, now);
  TEST_ASSERT_TRUE(tgt > now + 8 && tgt <= now + 8 + CPR);
  int64_t flap10 = -100000000LL + lroundf(10 * countsPerFlap(CPR, FLAPS));
  TEST_ASSERT_EQUAL(0, (int32_t)(((int64_t)tgt - flap10) % CPR));   // flap 10's position, whole revs on
}

static void test_across_counter_wrap() {
  // TIM2 wraps: positions just below INT32_MAX and just past it (negative) are a few counts apart.
  const int32_t MAX = 2147483647;
  TEST_ASSERT_EQUAL(10, countDiff(-2147483644, MAX - 5));    // 5 counts up to MAX, 5 more past the wrap
  TEST_ASSERT_EQUAL(-2147483644, countAdd(MAX - 5, 10));
  int32_t hz = MAX - 3000, now = MAX - 100;
  for (int flap = 0; flap < FLAPS; flap++) {
    int32_t tgt = flapTarget(hz, 37, CPR, FLAPS, 8, flap, now);
    int32_t ahead = countDiff(tgt, now);
    TEST_ASSERT_TRUE(ahead > 8 && ahead <= 8 + CPR);           // still the next one forward
    TEST_ASSERT_FLOAT_WITHIN(0.01f, (float)flap, currentFlap(tgt, hz, 37, CPR, FLAPS));
  }
}

static void test_current_flap() {
  float cpf = countsPerFlap(CPR, FLAPS);
  TEST_ASSERT_FLOAT_WITHIN(1e-4f, 0.0f, currentFlap(100 + 20, 100, 20, CPR, FLAPS));
  TEST_ASSERT_FLOAT_WITHIN(1.0f / cpf, 0.5f, currentFlap(120 + (int32_t)(cpf / 2), 100, 20, CPR, FLAPS));   // within a count
  TEST_ASSERT_FLOAT_WITHIN(1.0f / cpf, 3.0f, currentFlap(120 + lroundf(3 * cpf) + CPR, 100, 20, CPR, FLAPS));
  float back = currentFlap(120 - (int32_t)lroundf(cpf), 100, 20, CPR, FLAPS);   // one flap before flap 0
  TEST_ASSERT_FLOAT_WITHIN(1e-2f, 51.0f, back);
  for (int32_t c = -40000; c < 40000; c += 997) {
    float f = currentFlap(c, 100, 20, CPR, FLAPS);
    TEST_ASSERT_TRUE(f >= 0.0f && f < FLAPS);
  }
}

// ---------------------------------------------------------------- duties

static void test_ramp_up() {
  TEST_ASSERT_EQUAL(20, rampUpDuty(40, 20, 150, 0));
  TEST_ASSERT_EQUAL(30, rampUpDuty(40, 20, 150, 75));
  TEST_ASSERT_EQUAL(40, rampUpDuty(40, 20, 150, 150));
  TEST_ASSERT_EQUAL(40, rampUpDuty(40, 20, 150, 100000));
  TEST_ASSERT_EQUAL(40, rampUpDuty(40, 20, 0, 0));      // ramp off
  TEST_ASSERT_EQUAL(15, rampUpDuty(15, 20, 150, 0));    // top below slow: no ramp
}

static void test_move_duty() {
  // fast 40, slow 20, slow zone 210 counts, decel over the 200 before it
  TEST_ASSERT_EQUAL(40, moveDuty(40, 5000, 40, 20, 210, 200));
  TEST_ASSERT_EQUAL(40, moveDuty(40, 410, 40, 20, 210, 200));
  TEST_ASSERT_EQUAL(30, moveDuty(40, 310, 40, 20, 210, 200));
  TEST_ASSERT_EQUAL(20, moveDuty(40, 210, 40, 20, 210, 200));
  TEST_ASSERT_EQUAL(20, moveDuty(40, 209, 40, 20, 210, 200));
  TEST_ASSERT_EQUAL(20, moveDuty(40, 1, 40, 20, 210, 200));
  TEST_ASSERT_EQUAL(25, moveDuty(25, 310, 40, 20, 210, 200));   // still ramping up: the lower one wins
  TEST_ASSERT_EQUAL(40, moveDuty(40, 300, 40, 20, 210, 0));     // no decel zone
}

// ---------------------------------------------------------- self-test etc

static void test_test_verdict() {
  TEST_ASSERT_EQUAL(T_NOCOUNTS, testVerdict(0, 0));
  TEST_ASSERT_EQUAL(T_FEW, testVerdict(500, -5));
  TEST_ASSERT_EQUAL(T_FEW, testVerdict(19, -500));
  TEST_ASSERT_EQUAL(T_PASS, testVerdict(500, -480));
  TEST_ASSERT_EQUAL(T_BACKWARDS, testVerdict(-500, 480));
  TEST_ASSERT_EQUAL(T_SAMESIGN, testVerdict(500, 480));
  TEST_ASSERT_EQUAL(T_SAMESIGN, testVerdict(-500, -480));
}

static void test_learn_lead() {
  TEST_ASSERT_EQUAL(8, learnLead(8, 0));
  TEST_ASSERT_EQUAL(8, learnLead(8, 2));
  TEST_ASSERT_EQUAL(8, learnLead(8, -2));
  TEST_ASSERT_EQUAL(10, learnLead(8, 3));      // overshot 3: lead +2
  TEST_ASSERT_EQUAL(6, learnLead(8, -3));      // stopped 3 short: lead -2
  TEST_ASSERT_EQUAL(0, learnLead(8, -100));
  TEST_ASSERT_EQUAL(600, learnLead(590, 100));
}

// --------------------------------------------- equivalence with the old inline code

static uint32_t rng = 12345;
static int32_t rnd(int32_t lo, int32_t hi) {
  rng = rng * 1103515245u + 12345u;
  return lo + (int32_t)((rng >> 8) % (uint32_t)(hi - lo + 1));
}

static void test_equivalent_to_legacy() {
  for (int i = 0; i < 20000; i++) {
    int32_t cpr = rnd(100, 20000), flaps = rnd(1, 64), hz = rnd(-50000, 50000), foff = rnd(-500, 500);
    int32_t lead = rnd(0, 600), now = rnd(-100000, 100000), count = rnd(-100000, 100000);
    int flap = rnd(0, flaps - 1);
    TEST_ASSERT_EQUAL(legacy::flapTarget(hz, foff, cpr, flaps, lead, flap, now),
                      flapTarget(hz, foff, cpr, flaps, lead, flap, now));
    TEST_ASSERT_EQUAL_FLOAT(legacy::currentFlap(count, hz, foff, cpr, flaps),
                            currentFlap(count, hz, foff, cpr, flaps));
    int top = rnd(0, 100), slow = rnd(0, 100), ramp = rnd(-10, 500);
    uint32_t t = (uint32_t)rnd(0, 1000);
    TEST_ASSERT_EQUAL(legacy::rampUpDuty(top, slow, ramp, t), rampUpDuty(top, slow, ramp, t));
    int duty = rnd(0, 100), fast = rnd(0, 100), zone = rnd(0, 500), dzone = rnd(0, 500);
    int32_t rem = rnd(-100, 2000);
    TEST_ASSERT_EQUAL(legacy::moveDuty(duty, rem, fast, slow, zone, dzone), moveDuty(duty, rem, fast, slow, zone, dzone));
    int32_t f = rnd(-2000, 2000), b = rnd(-2000, 2000);
    TEST_ASSERT_EQUAL(legacy::testVerdict(f, b), testVerdict(f, b));
    int32_t err = rnd(-2000, 2000);
    TEST_ASSERT_EQUAL(legacy::learnLead(lead, err), learnLead(lead, err));
  }
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_wrap_flap);
  RUN_TEST(test_flap_target_window);
  RUN_TEST(test_flap_target_lands_on_flap);
  RUN_TEST(test_flap_target_never_goes_backwards);
  RUN_TEST(test_flap_target_extremes);
  RUN_TEST(test_across_counter_wrap);
  RUN_TEST(test_current_flap);
  RUN_TEST(test_ramp_up);
  RUN_TEST(test_move_duty);
  RUN_TEST(test_test_verdict);
  RUN_TEST(test_learn_lead);
  RUN_TEST(test_equivalent_to_legacy);
  return UNITY_END();
}
