// Module board v0.1 bring-up (STM32G031, ST-Link): pcb/module-board.
//
//   PC15 LED (active high)      PA0/PA1 ENC_A/B  TIM2 encoder mode (AF2)
//   PA6/PA7 MOT_IN1/IN2 TIM3    PA4 ISEN_ADC     PA5 HALL (low = magnet)
//   PA2/PA3 USART2 TX/RX -> J6 pads 6/7 (optional USB-UART)
//
// With no UART the LED is the whole UI:
//   Solid for 8 s after reset (LED self-test), then 1 Hz short blink = alive.   Solid ~150 ms = encoder moved or hall low.
//   Turn the motor shaft/drum by hand and the LED lights; pass the magnet and it lights.
// The motor stays OFF until a command runs. 's' (or any stall / 3 s timeout) stops it.
//
// Serial commands:  ?  help     p  print status      z  zero the count
//                   f<pct>  forward   r<pct>  reverse   (pct 5..60, default 25)
//                   s  stop (coast)   b  brake

#include <Arduino.h>

static const PinName PIN_ENCA = PA_0;
static const PinName PIN_ENCB = PA_1;

static const uint32_t PWM_HZ     = 20000;
static const uint32_t LED_TEST_MS = 8000;    // LED solid for 8 s after reset (self-test), then heartbeat
static const int      MAX_PCT    = 60;
static const uint32_t RUN_MS     = 3000;   // auto-stop
static const uint32_t STALL_MS   = 300;    // no counts while driven -> stop
static const float    R_SENSE    = 0.33f;  // R7; ISEN -> 1k + 100 nF -> ADC (DC gain 1)

Uart Dbg(PA_3, PA_2);                      // RX, TX (USART2)
static HardwareTimer *pwm;
static uint32_t D_HALL, D_ISEN;           // Arduino pin numbers for PA5 / PA4 (pinMode() wants these, not PinName)

// PC15 is not in the core's pin table: drive it straight from the registers.
static void ledInit() { __HAL_RCC_GPIOC_CLK_ENABLE(); GPIOC->MODER = (GPIOC->MODER & ~(3u << 30)) | (1u << 30); }
static void ledSet(bool on) { GPIOC->BSRR = on ? (1u << 15) : (1u << 31); }

enum Mode { COAST, FWD, REV, BRAKE };
static Mode     mode = COAST;
static int      duty = 0;
static uint32_t runStart = 0, lastMove = 0;
static uint32_t lastCount = 0;

static void encInit() {
  __HAL_RCC_TIM2_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  GPIO_InitTypeDef g = {};
  g.Pin = GPIO_PIN_0 | GPIO_PIN_1;
  g.Mode = GPIO_MODE_AF_PP;
  g.Pull = GPIO_NOPULL;                    // 10 k pull-ups on the board
  g.Speed = GPIO_SPEED_FREQ_LOW;
  g.Alternate = GPIO_AF2_TIM2;
  HAL_GPIO_Init(GPIOA, &g);
  TIM2->CR1 = 0;
  TIM2->PSC = 0;
  TIM2->ARR = 0xFFFFFFFF;
  TIM2->CCMR1 = (1 << 0) | (1 << 8) | (0x3 << 4) | (0x3 << 12);  // CC1S/CC2S = TI1/TI2, filter 8 samples
  TIM2->CCER = 0;                          // both non-inverted; flip CC1P if counts run backwards
  TIM2->SMCR = 3;                          // encoder mode 3: count on both edges of both inputs
  TIM2->CNT = 0;
  TIM2->CR1 = TIM_CR1_CEN;
}

static void drive(Mode m, int pct) {
  mode = m;
  duty = pct;
  switch (m) {
    case COAST: pwm->setCaptureCompare(1, 0, PERCENT_COMPARE_FORMAT);   pwm->setCaptureCompare(2, 0, PERCENT_COMPARE_FORMAT);   break;
    case FWD:   pwm->setCaptureCompare(1, pct, PERCENT_COMPARE_FORMAT); pwm->setCaptureCompare(2, 0, PERCENT_COMPARE_FORMAT);   break;
    case REV:   pwm->setCaptureCompare(1, 0, PERCENT_COMPARE_FORMAT);   pwm->setCaptureCompare(2, pct, PERCENT_COMPARE_FORMAT); break;
    case BRAKE: pwm->setCaptureCompare(1, 100, PERCENT_COMPARE_FORMAT); pwm->setCaptureCompare(2, 100, PERCENT_COMPARE_FORMAT); break;
  }
  if (m == FWD || m == REV) { runStart = lastMove = millis(); lastCount = TIM2->CNT; }
}

#ifdef MOTOR_AUTOTEST
// Boots, waits for the LED self-test, then: forward 1 s, pause 1 s, reverse 1 s, pause.
// Reports with the LED, repeated every ~3 s:
//   3 quick blinks = OK (forward counts rose, reverse counts fell)
//   2 blinks       = counts run backwards (flip CC1P in encInit or swap motor wires)
//   1 blink        = no encoder counts at all (check A/B/3V3/GND wires)
static int autoResult = 0;                  // 0 running, 1 none, 2 backwards, 3 ok
static void autoTest(uint32_t now) {
  static uint32_t t0 = 0; static int stage = 0; static int32_t c0, d1, d2;
  if (stage == 0 && now > 10000) { t0 = now; c0 = TIM2->CNT; drive(FWD, 50); stage = 1; }
  else if (stage == 1 && now - t0 > 1000) { d1 = (int32_t)TIM2->CNT - c0; drive(COAST, 0); t0 = now; stage = 2; }
  else if (stage == 2 && now - t0 > 1000) { c0 = TIM2->CNT; t0 = now; drive(REV, 50); stage = 3; }
  else if (stage == 3 && now - t0 > 1000) { d2 = (int32_t)TIM2->CNT - c0; drive(COAST, 0); stage = 4;
    autoResult = (d1 == 0 && d2 == 0) ? 1 : ((d1 > 0 && d2 < 0) ? 3 : 2);
    Dbg.printf("autotest: fwd %ld counts, rev %ld counts -> result %d\r\n", (long)d1, (long)d2, autoResult); }
}
#endif

static float senseMilliamps() {
  analogReadResolution(12);
  uint32_t s = 0;
  for (int i = 0; i < 16; i++) s += analogRead(D_ISEN);
  float v = (s / 16.0f) * 3.3f / 4095.0f;
  return v / R_SENSE * 1000.0f;
}

static void status() {
  const char *m[] = {"coast", "fwd", "rev", "brake"};
  Dbg.printf("mode=%s duty=%d%%  count=%ld  hall=%s  Isense=%.0f mA\r\n",
                 m[mode], duty, (long)(int32_t)TIM2->CNT,
                 digitalRead(D_HALL) ? "open" : "MAGNET", senseMilliamps());
}

static void help() {
  Dbg.println(F("p status | z zero | f<pct> fwd | r<pct> rev | s stop | b brake | ? help"));
}

static void command(String c) {
  c.trim();
  if (!c.length()) return;
  char k = c[0];
  int pct = c.length() > 1 ? c.substring(1).toInt() : 25;
  pct = constrain(pct, 5, MAX_PCT);
  switch (k) {
    case 'f': drive(FWD, pct); status(); break;
    case 'r': drive(REV, pct); status(); break;
    case 's': drive(COAST, 0); status(); break;
    case 'b': drive(BRAKE, 0); status(); break;
    case 'z': TIM2->CNT = 0; lastCount = 0; status(); break;
    case 'p': status(); break;
    default:  help();
  }
}

void setup() {
  D_HALL = pinNametoDigitalPin(PA_5);
  D_ISEN = pinNametoDigitalPin(PA_4);
  ledInit();
  pinMode(D_HALL, INPUT);                  // 10 k pull-up on the board
  pinMode(D_ISEN, INPUT_ANALOG);
  // Co-bonded pins (PB4/5/6, PB8, PC14, PA8, PB0-2) stay in their reset state (analog): design §7.1.

  // PA6/PA7 -> TIM3_CH1/CH2 (AF1), set up by hand: the core's pin-name lookup hangs on this variant.
  __HAL_RCC_GPIOA_CLK_ENABLE();
  GPIO_InitTypeDef g = {};
  g.Pin = GPIO_PIN_6 | GPIO_PIN_7;
  g.Mode = GPIO_MODE_AF_PP;
  g.Pull = GPIO_NOPULL;
  g.Speed = GPIO_SPEED_FREQ_LOW;
  g.Alternate = GPIO_AF1_TIM3;
  HAL_GPIO_Init(GPIOA, &g);
  pwm = new HardwareTimer(TIM3);
  pwm->setMode(1, TIMER_OUTPUT_COMPARE_PWM1, NC);
  pwm->setMode(2, TIMER_OUTPUT_COMPARE_PWM1, NC);
  pwm->setOverflow(PWM_HZ, HERTZ_FORMAT);
  pwm->resume();
  TIM3->CCER |= TIM_CCER_CC1E | TIM_CCER_CC2E;   // resume() leaves outputs off and the counter stopped with no bound pin
  TIM3->CR1  |= TIM_CR1_CEN;
  drive(COAST, 0);

  encInit();
  Dbg.begin(115200);
  Dbg.println(F("\r\nModule board v0.1 bring-up"));
  help();
}

void loop() {
  uint32_t now = millis();
  static uint32_t seen = 0, ledHold = 0;
  uint32_t cnt = TIM2->CNT;

  // LED: heartbeat, solid while counts move or the hall is active.
  if (cnt != seen) { seen = cnt; ledHold = now + 150; }
  if (digitalRead(D_HALL) == LOW) ledHold = now + 150;
  if (now < LED_TEST_MS) ledHold = LED_TEST_MS;  // LED solid after reset: LED self-test
  bool beat = (now % 1000) < 60;
#ifdef MOTOR_AUTOTEST
  autoTest(now);
  if (autoResult) {                          // report: N quick blinks every 3 s
    uint32_t ph = now % 3000;
    beat = ph < (uint32_t)autoResult * 300 && (ph % 300) < 150;
    ledHold = 0;
  }
#endif
  ledSet(now < ledHold || beat);

  // Motion guards.
  if (mode == FWD || mode == REV) {
    if (cnt != lastCount) { lastCount = cnt; lastMove = now; }
    if (now - lastMove > STALL_MS) { drive(COAST, 0); Dbg.println(F("STALL: no encoder counts, stopped (check A/B, 3V3, motor wires)")); }
    else if (now - runStart > RUN_MS) { drive(COAST, 0); Dbg.println(F("timeout, stopped")); status(); }
  }

  static String line;
  while (Dbg.available()) {
    char ch = Dbg.read();
    if (ch == '\n' || ch == '\r') { command(line); line = ""; }
    else line += ch;
  }
}
