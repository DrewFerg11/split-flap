// Bus protocol (firmware/shared/sfbus.h): CRC, framing, the byte parser, and the wire format.
// The ESP32 controller uses the same header, so a change here changes both ends.
#include <unity.h>
#include "sfbus.h"

using namespace sfbus;

void setUp() {}
void tearDown() {}

// Wire format: these structs go over the bus byte for byte. Changing a size breaks every module
// in the field and the controller at once, so it has to be deliberate (and bump FW_VERSION).
static_assert(sizeof(SetMsg) == 5, "SetMsg wire size");
static_assert(sizeof(Ping) == 13, "Ping wire size");
static_assert(sizeof(AssignMsg) == 13, "AssignMsg wire size");
static_assert(sizeof(AssignMsg) <= MAX_PAYLOAD, "AssignMsg fits one frame");
static_assert(sizeof(Status) == 26, "Status wire size");
static_assert(sizeof(Status) <= MAX_PAYLOAD, "Status fits one frame");
static_assert(K_COUNT * sizeof(int32_t) <= MAX_PAYLOAD, "C_GET settings fit one frame");
static_assert(MAX_FRAME == MAX_PAYLOAD + 6, "frame = sync addr cmd len payload crc crc");

static void test_crc16_modbus_check_value() {
  const uint8_t s[] = {'1', '2', '3', '4', '5', '6', '7', '8', '9'};
  TEST_ASSERT_EQUAL_HEX16(0x4B37, crc16(s, sizeof s));   // CRC-16/MODBUS check value
  TEST_ASSERT_EQUAL_HEX16(0xFFFF, crc16(s, 0));
}

static void test_encode_layout() {
  uint8_t out[MAX_FRAME];
  const uint8_t p[] = {0x11, 0x22, 0x33};
  size_t n = encode(out, 7, C_FLAP, p, sizeof p);
  TEST_ASSERT_EQUAL(9, n);
  TEST_ASSERT_EQUAL_HEX8(SYNC, out[0]);
  TEST_ASSERT_EQUAL(7, out[1]);
  TEST_ASSERT_EQUAL(C_FLAP, out[2]);
  TEST_ASSERT_EQUAL(3, out[3]);
  TEST_ASSERT_EQUAL_HEX8_ARRAY(p, out + 4, 3);
  uint16_t c = crc16(out + 1, 6);                        // addr..payload, low byte first
  TEST_ASSERT_EQUAL_HEX8(c & 0xFF, out[7]);
  TEST_ASSERT_EQUAL_HEX8(c >> 8, out[8]);
}

static void test_encode_clamps_payload() {
  uint8_t out[MAX_FRAME + 16], big[MAX_PAYLOAD + 10] = {};
  TEST_ASSERT_EQUAL(MAX_FRAME, encode(out, 1, C_SET, big, sizeof big));
  TEST_ASSERT_EQUAL(MAX_PAYLOAD, out[3]);
}

// Feeds a frame 1 ms per byte; returns how many bytes reported a complete frame.
static int feed(Parser &ps, const uint8_t *b, size_t n, uint32_t &t) {
  int done = 0;
  for (size_t i = 0; i < n; i++) done += ps.feed(b[i], t++);
  return done;
}

static void test_round_trip_all_lengths() {
  uint8_t out[MAX_FRAME], p[MAX_PAYLOAD];
  for (int i = 0; i < MAX_PAYLOAD; i++) p[i] = (uint8_t)(i * 37 + 5);
  for (int len = 0; len <= MAX_PAYLOAD; len++) {
    Parser ps;
    uint32_t t = 0;
    size_t n = encode(out, 42, C_SET, p, (uint8_t)len);
    for (size_t i = 0; i + 1 < n; i++) TEST_ASSERT_FALSE(ps.feed(out[i], t++));   // only the last byte completes
    TEST_ASSERT_TRUE(ps.feed(out[n - 1], t++));
    TEST_ASSERT_EQUAL(42, ps.frame().addr);
    TEST_ASSERT_EQUAL(C_SET, ps.frame().cmd);
    TEST_ASSERT_EQUAL(len, ps.frame().len);
    if (len) TEST_ASSERT_EQUAL_HEX8_ARRAY(p, ps.frame().data, len);
  }
}

static void test_skips_noise_before_sync() {
  Parser ps;
  uint32_t t = 0;
  const uint8_t junk[] = {0x00, 0x13, 0xFF, 0x5A};
  TEST_ASSERT_EQUAL(0, feed(ps, junk, sizeof junk, t));
  uint8_t out[MAX_FRAME];
  size_t n = encode(out, 3, C_PING, nullptr, 0);
  TEST_ASSERT_EQUAL(1, feed(ps, out, n, t));
  TEST_ASSERT_EQUAL(C_PING, ps.frame().cmd);
}

static void test_back_to_back_frames() {
  Parser ps;
  uint32_t t = 0;
  uint8_t a[MAX_FRAME], b[MAX_FRAME];
  uint8_t flap = 9;
  size_t na = encode(a, 1, C_FLAP, &flap, 1), nb = encode(b, 2, C_HOME, nullptr, 0);
  TEST_ASSERT_EQUAL(1, feed(ps, a, na, t));
  TEST_ASSERT_EQUAL(1, ps.frame().addr);
  TEST_ASSERT_EQUAL(1, feed(ps, b, nb, t));
  TEST_ASSERT_EQUAL(2, ps.frame().addr);
}

static void test_bad_crc_rejected_and_counted() {
  Parser ps;
  uint32_t t = 0;
  uint8_t out[MAX_FRAME];
  size_t n = encode(out, 5, C_STATUS, nullptr, 0);
  out[n - 1] ^= 0x01;
  TEST_ASSERT_EQUAL(0, feed(ps, out, n, t));
  TEST_ASSERT_EQUAL(1, ps.crcErrors);
  n = encode(out, 5, C_STATUS, nullptr, 0);               // and the parser recovers
  TEST_ASSERT_EQUAL(1, feed(ps, out, n, t));
}

static void test_oversize_length_dropped() {
  Parser ps;
  uint32_t t = 0;
  const uint8_t hdr[] = {SYNC, 1, C_SET, MAX_PAYLOAD + 1};
  TEST_ASSERT_EQUAL(0, feed(ps, hdr, sizeof hdr, t));
  uint8_t out[MAX_FRAME];
  size_t n = encode(out, 1, C_PING, nullptr, 0);
  TEST_ASSERT_EQUAL(1, feed(ps, out, n, t));
}

static void test_gap_inside_frame_drops_it() {
  Parser ps;
  uint8_t out[MAX_FRAME];
  uint8_t flap = 3;
  size_t n = encode(out, 1, C_FLAP, &flap, 1);
  uint32_t t = 0;
  for (size_t i = 0; i < 3; i++) ps.feed(out[i], t++);
  t += GAP_MS + 1;                                        // a pause longer than GAP_MS mid-frame
  bool done = false;
  for (size_t i = 3; i < n; i++) done |= ps.feed(out[i], t++);
  TEST_ASSERT_FALSE(done);
  TEST_ASSERT_EQUAL(1, feed(ps, out, n, t));              // a clean frame afterwards still parses
}

static void test_gap_of_exactly_gap_ms_is_kept() {
  Parser ps;
  uint8_t out[MAX_FRAME];
  size_t n = encode(out, 1, C_PING, nullptr, 0);
  uint32_t t = 0;
  bool done = false;
  for (size_t i = 0; i < n; i++) { done |= ps.feed(out[i], t); t += GAP_MS; }
  TEST_ASSERT_TRUE(done);
}

static void test_name_tables_match_enums() {
  TEST_ASSERT_EQUAL(M_TEST + 1, sizeof MODE_NAMES / sizeof MODE_NAMES[0]);
  TEST_ASSERT_EQUAL(T_BACKWARDS + 1, sizeof STOP_NAMES / sizeof STOP_NAMES[0]);
  for (int k = 0; k < K_COUNT; k++) {
    TEST_ASSERT_NOT_NULL(KEY_NAMES[k]);
    TEST_ASSERT_NOT_NULL(KEY_HELP[k]);
  }
}

static void test_defaults() {
  TEST_ASSERT_EQUAL(52, KEY_DEFAULTS[K_FLAPS]);
  TEST_ASSERT_EQUAL(10856, KEY_DEFAULTS[K_CPR]);
  // dir 0: every v0.1 board ran backwards with the bench rig's 1 (2026-10-29). Settings live on the
  // controller and are lost when it's swapped, so the compiled default is what a module falls back to.
  TEST_ASSERT_EQUAL(0, KEY_DEFAULTS[K_DIR]);
  TEST_ASSERT_EQUAL(0, KEY_DEFAULTS[K_ILIM]);             // jam cut-off off until ISEN is measured
  TEST_ASSERT_TRUE(KEY_DEFAULTS[K_SLOW] < KEY_DEFAULTS[K_FAST]);
}

// Discovery slots: in range, and the seed moves a module's slot, so two modules that clash get another try.
static void test_discover_slot_range_and_seed() {
  const uint32_t a[3] = {0x00410021, 0x12345678, 0x9ABCDEF0}, b[3] = {0x00410021, 0x12345678, 0x9ABCDEF1};
  int moved = 0, apart = 0;
  for (int seed = 0; seed < 256; seed++) {
    TEST_ASSERT_TRUE(discoverSlot(a, (uint8_t)seed) < DISCOVER_SLOTS);
    if (discoverSlot(a, (uint8_t)seed) != discoverSlot(a, (uint8_t)(seed + 1))) moved++;
    if (discoverSlot(a, (uint8_t)seed) != discoverSlot(b, (uint8_t)seed)) apart++;
  }
  TEST_ASSERT_TRUE(moved > 128);               // about 7/8 of seeds change the slot
  TEST_ASSERT_TRUE(apart > 128);               // two near-identical UIDs mostly land in different slots
}

// A Ping reply must fit inside one slot, or neighbouring slots would overlap on the wire (10 bits per byte).
static void test_ping_reply_fits_a_slot() {
  uint32_t wireUs = (uint32_t)(6 + sizeof(Ping)) * 10u * 1000000u / BAUD;
  TEST_ASSERT_TRUE(wireUs < SLOT_US);
}

static void test_enum_commands_follow_ident() {
  TEST_ASSERT_EQUAL(C_IDENT + 1, C_DISCOVER);  // new commands appended: the existing numbers didn't move
  TEST_ASSERT_EQUAL(C_DISCOVER + 1, C_ASSIGN);
  TEST_ASSERT_EQUAL(C_ASSIGN + 1, C_UNASSIGN);
  TEST_ASSERT_EQUAL(C_UNASSIGN + 1, C_ADVANCE);
  TEST_ASSERT_EQUAL(13, C_IDENT);
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_crc16_modbus_check_value);
  RUN_TEST(test_encode_layout);
  RUN_TEST(test_encode_clamps_payload);
  RUN_TEST(test_round_trip_all_lengths);
  RUN_TEST(test_skips_noise_before_sync);
  RUN_TEST(test_back_to_back_frames);
  RUN_TEST(test_bad_crc_rejected_and_counted);
  RUN_TEST(test_oversize_length_dropped);
  RUN_TEST(test_gap_inside_frame_drops_it);
  RUN_TEST(test_gap_of_exactly_gap_ms_is_kept);
  RUN_TEST(test_name_tables_match_enums);
  RUN_TEST(test_defaults);
  RUN_TEST(test_discover_slot_range_and_seed);
  RUN_TEST(test_ping_reply_fits_a_slot);
  RUN_TEST(test_enum_commands_follow_ident);
  return UNITY_END();
}
