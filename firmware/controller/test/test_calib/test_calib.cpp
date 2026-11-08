// Calibration maths (lib/sfctl_core/calib.h): counts per rev from hall edges, rescaling settings kept in
// counts, and the flap offset for "here".
#include <unity.h>
#include "calib.h"

using namespace sfctl::calib;

void setUp() {}
void tearDown() {}

static void test_cpr_from_edges() {
  const int32_t e[] = {1000, 11856, 22711, 33568};               // revs of 10856, 10855, 10857
  TEST_ASSERT_EQUAL(10856, cprFromEdges(e, 3));
  TEST_ASSERT_EQUAL(1, revSpread(e, 3, 10856));
  const int32_t one[] = {-500, 10356};
  TEST_ASSERT_EQUAL(10856, cprFromEdges(one, 1));
  TEST_ASSERT_EQUAL(0, revSpread(one, 1, 10856));
}

static void test_rescale_keeps_share_of_a_flap() {
  TEST_ASSERT_EQUAL(210, rescale(210, 10856, 10856));
  TEST_ASSERT_EQUAL(105, rescale(210, 5428, 10856));             // half the counts per rev: half the zone
  TEST_ASSERT_EQUAL(16, rescale(8, 21712, 10856));
  TEST_ASSERT_EQUAL(-37, rescale(-37, 10856, 10856));
}

static void test_foff_for_here() {
  // 52 flaps, 10856 counts: 208.77 counts per flap
  TEST_ASSERT_EQUAL(0, foffForHere(0, 0.0f, 0, 52, 10856));
  TEST_ASSERT_EQUAL(209, foffForHere(0, 1.0f, 0, 52, 10856));    // reading flap 1 but it shows flap 0
  TEST_ASSERT_EQUAL(-209, foffForHere(0, 51.0f, 0, 52, 10856));  // shortest way round: -1 flap, not +51
  TEST_ASSERT_EQUAL(100 + 104, foffForHere(100, 10.5f, 10, 52, 10856));
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_cpr_from_edges);
  RUN_TEST(test_rescale_keeps_share_of_a_flap);
  RUN_TEST(test_foff_for_here);
  return UNITY_END();
}
