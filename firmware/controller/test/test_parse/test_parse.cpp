// Console line parsing (include/console_parse.h): address prefixes, glued arguments, ';' lists.
#include <unity.h>
#include "console_parse.h"

using namespace console;

static const uint8_t BCAST = 0xFF, MAXA = 32;

void setUp() {}
void tearDown() {}

static Parsed parse(const char *s, uint8_t cur = 1) {
  Parsed p;
  TEST_ASSERT_TRUE(parseLine(s, cur, BCAST, MAXA, p));
  return p;
}

static void test_plain_command_uses_selected_module() {
  Parsed p = parse("home", 3);
  TEST_ASSERT_EQUAL(3, p.addr);
  TEST_ASSERT_FALSE(p.explicitAddr);
  TEST_ASSERT_EQUAL_STRING("home", p.cmd.c_str());
  TEST_ASSERT_FALSE(p.hasArg);
}

static void test_address_prefix() {
  Parsed p = parse("2 f 17");
  TEST_ASSERT_EQUAL(2, p.addr);
  TEST_ASSERT_TRUE(p.explicitAddr);
  TEST_ASSERT_EQUAL_STRING("f", p.cmd.c_str());
  TEST_ASSERT_EQUAL(17, p.arg);
  TEST_ASSERT_EQUAL(BCAST, parse("* f 5").addr);
  TEST_ASSERT_EQUAL(MAXA, parse("99 home").addr);                // clamped to 1..32
  TEST_ASSERT_EQUAL(1, parse("0 home").addr);
}

static void test_bare_address_means_status() {
  Parsed p = parse("4");
  TEST_ASSERT_EQUAL(4, p.addr);
  TEST_ASSERT_EQUAL_STRING("s", p.cmd.c_str());
}

static void test_glued_argument() {
  Parsed p = parse("f7");
  TEST_ASSERT_EQUAL_STRING("f", p.cmd.c_str());
  TEST_ASSERT_EQUAL(7, p.arg);
  p = parse("d-25");
  TEST_ASSERT_EQUAL_STRING("d", p.cmd.c_str());
  TEST_ASSERT_EQUAL(-25, p.arg);
  p = parse("3 f12");
  TEST_ASSERT_EQUAL(3, p.addr);
  TEST_ASSERT_EQUAL(12, p.arg);
}

static void test_case_whitespace_and_rest() {
  Parsed p = parse("  SET  Lead 12  ");
  TEST_ASSERT_EQUAL_STRING("set", p.cmd.c_str());
  TEST_ASSERT_EQUAL_STRING("lead 12", p.rest.c_str());
  TEST_ASSERT_TRUE(p.hasArg);
  TEST_ASSERT_EQUAL(0, p.arg);                                   // "lead 12" isn't a number
  Parsed q;
  TEST_ASSERT_FALSE(parseLine("   ", 1, BCAST, MAXA, q));
}

static void test_split_commands() {
  auto v = splitCommands("3 f 1; 1 f 2;x");
  TEST_ASSERT_EQUAL(3, v.size());
  TEST_ASSERT_EQUAL_STRING("3 f 1", v[0].c_str());
  TEST_ASSERT_EQUAL_STRING(" 1 f 2", v[1].c_str());
  TEST_ASSERT_EQUAL_STRING("x", v[2].c_str());
  TEST_ASSERT_EQUAL(1, splitCommands("home").size());
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_plain_command_uses_selected_module);
  RUN_TEST(test_address_prefix);
  RUN_TEST(test_bare_address_means_status);
  RUN_TEST(test_glued_argument);
  RUN_TEST(test_case_whitespace_and_rest);
  RUN_TEST(test_split_commands);
  return UNITY_END();
}
