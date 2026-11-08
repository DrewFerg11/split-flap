// Serial console line parsing: hardware-free, so the native unit tests can run it.
//   "[addr] cmd [args]"   addr = 1..MAX_ADDR or * (broadcast); no addr = the selected module
//   "f7", "d-25"          a number glued to the command is split off
//   "3 f 1; 1 f 2"        several commands on one line (splitCommands)
#pragma once
#include <ctype.h>
#include <stdint.h>
#include <stdlib.h>
#include <string>
#include <vector>

namespace console {

struct Parsed {
  uint8_t     addr = 0;            // target module, or bcast
  bool        explicitAddr = false;
  std::string cmd;                 // lower case
  std::string rest;                // everything after the command, trimmed
  bool        hasArg = false;
  long        arg = 0;             // rest as a number (0 when it isn't one)
};

inline std::string trim(const std::string &s) {
  size_t a = 0, b = s.size();
  while (a < b && isspace((unsigned char)s[a])) a++;
  while (b > a && isspace((unsigned char)s[b - 1])) b--;
  return s.substr(a, b - a);
}

inline long toInt(const std::string &s) { return atol(s.c_str()); }   // as Arduino String::toInt

inline std::vector<std::string> splitCommands(const std::string &line) {
  std::vector<std::string> out;
  size_t start = 0;
  for (size_t i = 0; i <= line.size(); i++)
    if (i == line.size() || line[i] == ';') { out.push_back(line.substr(start, i - start)); start = i + 1; }
  return out;
}

// Returns false for an empty line. `cur` is the selected module, `bcast` the broadcast address.
inline bool parseLine(std::string line, uint8_t cur, uint8_t bcast, uint8_t maxAddr, Parsed &p) {
  line = trim(line);
  for (auto &c : line) c = (char)tolower((unsigned char)c);
  if (line.empty()) return false;

  p = Parsed();
  p.addr = cur;
  if (line[0] == '*' || isdigit((unsigned char)line[0])) {        // optional address prefix
    size_t sp = line.find(' ');
    std::string a = sp == std::string::npos ? line : line.substr(0, sp);
    if (a == "*") p.addr = bcast;
    else {
      long v = toInt(a);
      p.addr = (uint8_t)(v < 1 ? 1 : v > maxAddr ? maxAddr : v);
    }
    p.explicitAddr = true;
    line = sp == std::string::npos ? std::string("s") : trim(line.substr(sp + 1));   // bare address = status
  }
  size_t sp = line.find(' ');
  if (sp == std::string::npos) {                                   // accept "f7", "d-25"
    for (size_t i = 1; i < line.size(); i++)
      if (isdigit((unsigned char)line[i]) || line[i] == '-') { line = line.substr(0, i) + " " + line.substr(i); sp = i; break; }
  }
  p.cmd = sp == std::string::npos ? line : line.substr(0, sp);
  p.rest = sp == std::string::npos ? "" : trim(line.substr(sp + 1));
  p.hasArg = !p.rest.empty();
  p.arg = toInt(p.rest);
  return true;
}

}  // namespace console
