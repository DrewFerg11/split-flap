// Split-flap module firmware (STM32G031, pcb/module-board), bench version 1.
// RS-485 slave. Motion logic ported from the N20 bench sketch.
//
// Addressing: the default build is the same image on every board. It powers up unplaced (address 0) and the
// host places it over the bus, in ENUM chain order (sfbus.h).
//
//   PC15 LED                    PA0/PA1 ENC_A/B  TIM2 encoder mode (AF2)
//   PA6/PA7 MOT_IN1/IN2 TIM3    PA4 ISEN_ADC     PA5 HALL (low = magnet, EXTI)
//   PA9/PA10/PB3 USART1 bus     PB7 ENUM_IN      PB9 ENUM_OUT
//
// LED: unplaced = 2 Hz blink. Once placed, N blinks = this board's address, then a 1 Hz heartbeat. Lit while
// the motor runs and briefly on every frame addressed to it. C_IDENT blinks it fast for 3 s.
//
// Motor drive is slow decay (drive / brake PWM), like the TB6612 on the bench rig, so the bench duty
// settings carry over. One direction pin is held high and the other PWMs: IN low = drive, IN high = brake.
#ifndef SFBUS_BRIDGE
#include <Arduino.h>
#include "sfbus.h"
#include "motion.h"
#include "usart.h"

using namespace sfbus;

static const uint32_t PWM_HZ        = 20000;
static const uint32_t REPLY_DELAY_US = 500;    // let the host turn its transceiver round
static const uint32_t SETTLE_MS     = 200;
static const uint32_t DRIVE_MAX_MS  = 10000;
static const uint32_t ILIM_HOLD_MS  = 250;

static int32_t cfg[K_COUNT];
static Parser  parser;
static uint32_t D_HALL, D_ISEN;
static uint32_t pwmTop;                        // ARR + 1

// --------------------------------------------------------------- state ---

static uint8_t  myAddr = ADDR_NEW;             // 0 = not placed yet
static uint32_t placedMs = 0;                  // when the address was taken (LED blink count starts here)
static uint8_t  mode = M_IDLE;
static uint8_t  stopReason = R_NONE;
static bool     fresh = true;                  // no SET since reset
static bool     homed = false;
static int32_t  hallZero = 0;
static int32_t  target = 0;
static uint8_t  targetFlap = 255;
static int      dutyPct = 0;
static int32_t  lastErr = 0, aux = 0;
static uint32_t moveStartMs = 0, lastMoveMs = 0;
static int32_t  moveStartCount = 0, lastSeenCount = 0;
static uint32_t settleUntil = 0;
enum Settle { S_MOVE, S_HOME, S_STOP };
static Settle   settleKind = S_STOP;
static uint32_t identUntil = 0, rxFlashUntil = 0;
static uint32_t milliamps = 0, peakmA = 0, overSince = 0;
static int      testStage = 0;
static uint32_t testT0 = 0;
static int32_t  testC0 = 0, testC1 = 0;

static volatile bool     hallHit = false;
static volatile int32_t  hallRaw = 0;
static volatile uint32_t hallEdges = 0;

// ---------------------------------------------------------------- ENUM ---

static bool enumIn() { return GPIOB->IDR & (1u << 7); }
static void enumOut(bool on) { GPIOB->BSRR = on ? (1u << 9) : (1u << 25); }

// ----------------------------------------------------------------- LED ---

static void ledInit() { __HAL_RCC_GPIOC_CLK_ENABLE(); GPIOC->MODER = (GPIOC->MODER & ~(3u << 30)) | (1u << 30); }
static void ledSet(bool on) { GPIOC->BSRR = on ? (1u << 15) : (1u << 31); }

// ------------------------------------------------------------- encoder ---

static void encInit() {
  __HAL_RCC_TIM2_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  GPIO_InitTypeDef g = {};
  g.Pin = GPIO_PIN_0 | GPIO_PIN_1;
  g.Mode = GPIO_MODE_AF_PP;
  g.Pull = GPIO_NOPULL;                        // 10 k pull-ups on the board
  g.Speed = GPIO_SPEED_FREQ_LOW;
  g.Alternate = GPIO_AF2_TIM2;
  HAL_GPIO_Init(GPIOA, &g);
  TIM2->CR1 = 0;
  TIM2->PSC = 0;
  TIM2->ARR = 0xFFFFFFFF;
  TIM2->CCMR1 = (1 << 0) | (1 << 8) | (0x3 << 4) | (0x3 << 12);  // TI1/TI2, filter 8 samples
  TIM2->CCER = 0;
  TIM2->SMCR = 3;                              // encoder mode 3: both edges of both inputs
  TIM2->CNT = 0;
  TIM2->CR1 = TIM_CR1_CEN;
}

// + = forward (flaps falling). Board #1: IN1 drive made the raw count rise; 'dir' flips both together.
static int32_t toFwd(int32_t raw) { return cfg[K_DIR] ? -raw : raw; }
static int32_t enc() { return toFwd((int32_t)TIM2->CNT); }

// ---------------------------------------------------------------- hall ---

static void hallIsr() {
  hallEdges++;
  if (!hallHit) { hallRaw = (int32_t)TIM2->CNT; hallHit = true; }
}
static bool hallActive() { return digitalRead(D_HALL) == LOW; }

// --------------------------------------------------------------- motor ---

static void pwmInit() {
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_TIM3_CLK_ENABLE();
  GPIO_InitTypeDef g = {};
  g.Pin = GPIO_PIN_6 | GPIO_PIN_7;
  g.Mode = GPIO_MODE_AF_PP;
  g.Pull = GPIO_NOPULL;
  g.Speed = GPIO_SPEED_FREQ_LOW;
  g.Alternate = GPIO_AF1_TIM3;
  HAL_GPIO_Init(GPIOA, &g);
  pwmTop = HAL_RCC_GetPCLK1Freq() / PWM_HZ;    // APB prescaler 1: timer clock = PCLK
  TIM3->CR1 = 0;
  TIM3->PSC = 0;
  TIM3->ARR = pwmTop - 1;
  TIM3->CCR1 = 0;
  TIM3->CCR2 = 0;
  TIM3->CCMR1 = (6u << TIM_CCMR1_OC1M_Pos) | TIM_CCMR1_OC1PE | (6u << TIM_CCMR1_OC2M_Pos) | TIM_CCMR1_OC2PE;  // PWM1
  TIM3->CCER = TIM_CCER_CC1E | TIM_CCER_CC2E;
  TIM3->EGR = TIM_EGR_UG;
  TIM3->CR1 = TIM_CR1_ARPE | TIM_CR1_CEN;
}

static void setDuty(int pct) {                 // signed: + forward, - reverse, 0 coast
  pct = constrain(pct, -100, 100);
  dutyPct = pct;
  if (pct == 0) { TIM3->CCR1 = 0; TIM3->CCR2 = 0; return; }
  bool in1 = (pct > 0) != (cfg[K_DIR] != 0);   // drive OUT1 high (raw count rises)
  uint32_t pwm = pwmTop * (uint32_t)(100 - abs(pct)) / 100;   // share of the period spent braking
  if (in1) { TIM3->CCR1 = pwmTop; TIM3->CCR2 = pwm; }
  else     { TIM3->CCR2 = pwmTop; TIM3->CCR1 = pwm; }
}

static void brake() { dutyPct = 0; TIM3->CCR1 = pwmTop; TIM3->CCR2 = pwmTop; }

static void settle(Settle kind, uint32_t now) {
  brake();
  mode = M_SETTLE;
  settleKind = kind;
  settleUntil = now + (kind == S_STOP ? 100 : SETTLE_MS);
}

static void stopNow(uint8_t why) {
  stopReason = why;
  testStage = 0;
  settle(S_STOP, millis());
}

static void startMotion(uint8_t m, int pct) {
  uint32_t now = millis();
  mode = m;
  stopReason = R_NONE;
  peakmA = 0;
  overSince = 0;
  moveStartMs = lastMoveMs = now;
  moveStartCount = lastSeenCount = enc();
  setDuty(m == M_DRIVE || cfg[K_RAMP] <= 0 ? pct : min(pct, (int)cfg[K_SLOW]));   // MOVE/HOMING ramp up
}

static int rampUpDuty(int top, uint32_t now) {
  return motion::rampUpDuty(top, cfg[K_SLOW], cfg[K_RAMP], now - moveStartMs);
}

// ---------------------------------------------------------- flap maths ---
// (include/motion.h, unit-tested)

static int32_t flapTarget(int flap) {          // next forward position showing this flap
  return motion::flapTarget(hallZero, cfg[K_FOFF], cfg[K_CPR], cfg[K_FLAPS], cfg[K_LEAD], flap, enc());
}

static float currentFlap() {
  return motion::currentFlap(enc(), hallZero, cfg[K_FOFF], cfg[K_CPR], cfg[K_FLAPS]);
}

static void goFlap(int flap) {
  if (!homed) { stopReason = R_NOTHOMED; return; }
  flap = motion::wrapFlap(flap, cfg[K_FLAPS]);
  targetFlap = flap;
  target = flapTarget(flap);
  startMotion(M_MOVE, cfg[K_FAST]);
}

static void moveBy(int32_t delta) {
  if (delta <= 0) return;                      // forward only: flaps only fall one way
  target = motion::countAdd(enc(), delta);
  targetFlap = 255;
  startMotion(M_MOVE, cfg[K_FAST]);
}

// ---------------------------------------------------------- bus replies ---

static void replyFrom(uint8_t addr, uint8_t cmd, const void *p, uint8_t n) {
  uint8_t buf[MAX_FRAME];
  size_t len = encode(buf, addr, cmd | REPLY, p, n);
  delayMicroseconds(REPLY_DELAY_US);
  bus_write(buf, len);
}

static void reply(uint8_t cmd, const void *p, uint8_t n) { replyFrom(myAddr, cmd, p, n); }

static void replyStatus(uint8_t cmd) {
  Status s = {};
  s.fw = FW_VERSION;
  s.mode = mode;
  s.flags = (homed ? F_HOMED : 0) | (hallActive() ? F_HALL : 0) | (fresh ? F_FRESH : 0)
          | ((GPIOB->IDR & (1u << 7)) ? F_ENUM : 0);
  s.stop = stopReason;
  s.count = enc();
  s.flapX100 = homed ? (int16_t)lroundf(currentFlap() * 100) : -1;
  s.lastErr = constrain(lastErr, -32768, 32767);
  s.aux = constrain(aux, -32768, 32767);
  s.duty = dutyPct;
  s.target = targetFlap;
  s.mA = milliamps;
  s.peakmA = peakmA;
  s.lead = cfg[K_LEAD];
  s.uptimeMs = millis();
  reply(cmd, &s, sizeof s);
}

// C_DISCOVER / C_ASSIGN, sent to address 0. Only a module that is not placed and has ENUM_IN high takes part.
static void handleEnum(const Frame &f) {
  if (myAddr != ADDR_NEW || !enumIn()) return;
  uint32_t uid[3] = { HAL_GetUIDw0(), HAL_GetUIDw1(), HAL_GetUIDw2() };
  Ping me = { FW_VERSION, {} };
  memcpy(me.uid, uid, sizeof uid);
  if (f.cmd == C_DISCOVER) {
    if (f.len < 1) return;
    delayMicroseconds(discoverSlot(uid, f.data[0]) * SLOT_US);
    replyFrom(ADDR_NEW, f.cmd, &me, sizeof me);
  } else {
    if (f.len < sizeof(AssignMsg)) return;
    AssignMsg m;
    memcpy(&m, f.data, sizeof m);
    if (memcmp(m.uid, uid, sizeof uid) != 0 || m.addr < 1 || m.addr > ADDR_MAX) return;
    myAddr = m.addr;
    placedMs = millis();                       // ENUM_OUT stays low until C_ADVANCE
    replyFrom(myAddr, f.cmd, &me, sizeof me);
  }
}

static void handle(const Frame &f) {
  if (f.cmd & REPLY) return;
  if (f.cmd == C_DISCOVER || f.cmd == C_ASSIGN) { if (f.addr == ADDR_NEW) handleEnum(f); return; }
  if (f.cmd == C_UNASSIGN) {
    if (f.addr == ADDR_BCAST) {
      if (mode != M_IDLE) stopNow(R_USER);
      myAddr = ADDR_NEW;
      enumOut(false);
    }
    return;
  }
  if (f.cmd == C_ADVANCE) {                    // the next module in the row may now be placed
    if (f.addr == ADDR_BCAST && myAddr != ADDR_NEW) enumOut(true);
    return;
  }
  if (myAddr == ADDR_NEW) return;              // not placed: only the enumeration commands above
  bool mine = f.addr == myAddr;
  if (!mine && f.addr != ADDR_BCAST) return;
  rxFlashUntil = millis() + 40;

  switch (f.cmd) {
    case C_PING: {
      if (!mine) return;
      Ping p = { FW_VERSION, { HAL_GetUIDw0(), HAL_GetUIDw1(), HAL_GetUIDw2() } };
      reply(f.cmd, &p, sizeof p);
      return;
    }
    case C_GET:
      if (mine) reply(f.cmd, cfg, sizeof cfg);
      return;
    case C_STATUS: break;
    case C_STOP:  if (mode != M_IDLE && mode != M_SETTLE) stopNow(R_USER); else stopReason = R_USER; break;
    case C_HOME:
      hallHit = false;
      startMotion(M_HOMING, cfg[K_HOME]);
      break;
    case C_FLAP:  if (f.len >= 1) goFlap(f.data[0]); break;
    case C_DRIVE:
      if (f.len >= 1) {
        int8_t pct = (int8_t)f.data[0];
        if (pct == 0) stopNow(R_USER); else startMotion(M_DRIVE, pct);
      }
      break;
    case C_MOVE:  if (f.len >= 4) { int32_t d; memcpy(&d, f.data, 4); moveBy(d); } break;
    case C_REV:   if (f.len >= 2) { int16_t n; memcpy(&n, f.data, 2); moveBy((int32_t)n * cfg[K_CPR]); } break;
    case C_SET:
      if (f.len >= sizeof(SetMsg)) {
        SetMsg m; memcpy(&m, f.data, sizeof m);
        if (m.key < K_COUNT) {
          if (m.key == K_DIR && (m.value != 0) != (cfg[K_DIR] != 0)) homed = false;   // count sign flips
          cfg[m.key] = m.value;
          if (cfg[K_FLAPS] < 1) cfg[K_FLAPS] = 1;
          if (cfg[K_CPR] < 1) cfg[K_CPR] = 1;
          fresh = false;
        }
      }
      break;
    case C_ZERO:  TIM2->CNT = 0; homed = false; break;
    case C_TEST:
      if (mode == M_IDLE) { mode = M_TEST; testStage = 1; testT0 = millis(); testC0 = enc(); stopReason = R_NONE; setDuty(30); }
      break;
    case C_IDENT: identUntil = millis() + 3000; break;
    default: return;
  }
  if (mine) replyStatus(f.cmd);
}

// ----------------------------------------------------------- self-test ---
// Forward 30 % for 250 ms, brake, reverse 250 ms, brake. Same verdicts as the N20 bench 'test'.

static void testStep(uint32_t now) {
  uint32_t t = now - testT0;
  if (testStage == 1 && t >= 250)  { brake(); testStage = 2; }
  else if (testStage == 2 && t >= 400) { testC1 = enc(); setDuty(-30); testStage = 3; }
  else if (testStage == 3 && t >= 650) { brake(); testStage = 4; }
  else if (testStage == 4 && t >= 800) {
    int32_t c2 = enc();
    setDuty(0);
    testStage = 0;
    mode = M_IDLE;
    int32_t fwd = motion::countDiff(testC1, testC0), back = motion::countDiff(c2, testC1);
    lastErr = fwd; aux = back;
    stopReason = motion::testVerdict(fwd, back);
  }
}

// ---------------------------------------------------------------- main ---

void setup() {
  for (int i = 0; i < K_COUNT; i++) cfg[i] = KEY_DEFAULTS[i];
  ledInit();
  pwmInit();                                   // motor coasting before anything else
  encInit();

  D_HALL = pinNametoDigitalPin(PA_5);
  D_ISEN = pinNametoDigitalPin(PA_4);
  pinMode(D_HALL, INPUT);                      // 10 k pull-up on the board
  pinMode(D_ISEN, INPUT_ANALOG);
  analogReadResolution(12);
  attachInterrupt(D_HALL, hallIsr, FALLING);

  __HAL_RCC_GPIOB_CLK_ENABLE();                // PB7 ENUM_IN: input with pull-down
  GPIOB->MODER &= ~(3u << 14);
  GPIOB->PUPDR = (GPIOB->PUPDR & ~(3u << 14)) | (2u << 14);
  enumOut(false);                              // PB9 ENUM_OUT: output, low until this module is placed
  GPIOB->MODER = (GPIOB->MODER & ~(3u << 18)) | (1u << 18);
  // Co-bonded pins (PB8, PC14, PA8, PB0-2, PA11/12, PA15, PB4-6) stay analog: design §7.1.

  bus_init(BAUD);
}

void loop() {
  int b;
  while ((b = bus_read()) >= 0)
    if (parser.feed((uint8_t)b, millis())) handle(parser.frame());

  uint32_t now = millis();
  int32_t c = enc();

  // motor current: one ADC read every 5 ms, light filter. ISEN only sees current while driving
  // (not during the brake part of each PWM period), so this reads roughly I x duty.
  static uint32_t adcMs = 0;
  if (now - adcMs >= 5) {
    adcMs = now;
    uint32_t mA = (uint32_t)analogRead(D_ISEN) * 10000u / 4095u;   // 3.3 V / 0.33 ohm full scale
    milliamps = (milliamps * 3 + mA) / 4;
    bool running = mode == M_DRIVE || mode == M_MOVE || mode == M_HOMING;
    if (running && milliamps > peakmA) peakmA = milliamps;
    if (running && cfg[K_ILIM] > 0 && milliamps > (uint32_t)cfg[K_ILIM]) {
      if (!overSince) overSince = now;
      else if (now - overSince > ILIM_HOLD_MS) stopNow(R_OVERCURRENT);
    } else overSince = 0;
  }

  // hall: noise guard (a real pass is 2 edges per drum rev), then homing
  static uint32_t noiseMs = 0, noiseEdges = 0;
  static bool noisy = false;
  if (now - noiseMs >= 1000) {
    noisy = hallEdges - noiseEdges > 40;
    noiseEdges = hallEdges; noiseMs = now;
    if (noisy && mode == M_HOMING) stopNow(R_HALLNOISE);
  }
  if (mode == M_HOMING && hallHit && !noisy) {
    hallZero = toFwd(hallRaw);
    homed = true;
    stopReason = R_HOMED;
    settle(S_HOME, now);
  }

  if (mode == M_MOVE) {
    int32_t remaining = motion::countDiff(target, c);
    int fast = cfg[K_FAST], slow = cfg[K_SLOW], zone = cfg[K_ZONE], dzone = cfg[K_DZONE];
    if (remaining <= cfg[K_LEAD]) {
      stopReason = R_DONE;
      settle(S_MOVE, now);
    } else {
      int duty = motion::moveDuty(rampUpDuty(fast, now), remaining, fast, slow, zone, dzone);
      if (duty != dutyPct) setDuty(duty);
    }
  } else if (mode == M_HOMING) {
    int duty = rampUpDuty(cfg[K_HOME], now);
    if (duty != dutyPct) setDuty(duty);
    if (motion::countDiff(c, moveStartCount) > 2 * cfg[K_CPR]) stopNow(R_NOHALL);
  } else if (mode == M_DRIVE) {
    if (now - moveStartMs > DRIVE_MAX_MS) stopNow(R_TIMEOUT);
  } else if (mode == M_TEST) {
    testStep(now);
  }

  // stall watchdog
  if (mode == M_DRIVE || mode == M_MOVE || mode == M_HOMING) {
    if (c != lastSeenCount) { lastSeenCount = c; lastMoveMs = now; }
    else if (now - moveStartMs > 400 && now - lastMoveMs > (uint32_t)cfg[K_STALL]) stopNow(R_STALL);
  }

  // settled: coast, record where it stopped
  if (mode == M_SETTLE && (int32_t)(now - settleUntil) >= 0) {
    setDuty(0);
    mode = M_IDLE;
    if (settleKind == S_HOME) {
      aux = motion::countDiff(c, hallZero);
      if (cfg[K_REST] >= 0) goFlap(cfg[K_REST]);
    } else if (settleKind == S_MOVE) {
      int32_t err = motion::countDiff(c, target);
      lastErr = err;
      if (cfg[K_AUTO]) cfg[K_LEAD] = motion::learnLead(cfg[K_LEAD], err);
    }
  }

  // LED: unplaced = 2 Hz; address blinks once placed, then heartbeat; lit while moving / on traffic; fast blink to identify
  bool led;
  uint32_t since = now - placedMs;
  if (now < identUntil)            led = (now % 200) < 100;
  else if (myAddr == ADDR_NEW)     led = (now % 500) < 250;
  else if (since < 600u * myAddr + 500) led = since >= 500 && ((since - 500) % 600) < 300;
  else                             led = mode != M_IDLE || now < rxFlashUntil || (now % 1000) < 60;
  ledSet(led);
}
#endif
