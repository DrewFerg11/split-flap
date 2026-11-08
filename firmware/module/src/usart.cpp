#include <Arduino.h>
#include "usart.h"

namespace {

struct Ring {
  volatile uint8_t buf[256];
  volatile uint8_t head = 0, tail = 0;
  void push(uint8_t b) { uint8_t h = head + 1; if (h != tail) { buf[head] = b; head = h; } }   // full: drop
  int pop() { if (head == tail) return -1; uint8_t b = buf[tail]; tail = tail + 1; return b; }
};

Ring busRx, dbgRx;

void rxIsr(USART_TypeDef *u, Ring &r) {
  uint32_t isr = u->ISR;
  if (isr & (USART_ISR_ORE | USART_ISR_FE | USART_ISR_NE | USART_ISR_PE))
    u->ICR = USART_ICR_ORECF | USART_ICR_FECF | USART_ICR_NECF | USART_ICR_PECF;
  while (u->ISR & USART_ISR_RXNE_RXFNE) r.push((uint8_t)u->RDR);
}

void pinAf(GPIO_TypeDef *port, uint32_t pin, uint32_t af, uint32_t pull) {
  GPIO_InitTypeDef g = {};
  g.Pin = pin;
  g.Mode = GPIO_MODE_AF_PP;
  g.Pull = pull;
  g.Speed = GPIO_SPEED_FREQ_HIGH;
  g.Alternate = af;
  HAL_GPIO_Init(port, &g);
}

void write(USART_TypeDef *u, const uint8_t *p, uint16_t n) {
  while (n--) {
    while (!(u->ISR & USART_ISR_TXE_TXFNF)) {}
    u->TDR = *p++;
  }
  while (!(u->ISR & USART_ISR_TC)) {}
}

}  // namespace

extern "C" void USART1_IRQHandler(void) { rxIsr(USART1, busRx); }
extern "C" void USART2_IRQHandler(void) { rxIsr(USART2, dbgRx); }

void bus_init(uint32_t baud) {
  __HAL_RCC_SYSCFG_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_USART1_CLK_ENABLE();
  // TSSOP-20 pins 16/17 are bonded to PA11/PA12; remap them to PA9/PA10 (design §7.1).
  SYSCFG->CFGR1 |= SYSCFG_CFGR1_PA11_RMP | SYSCFG_CFGR1_PA12_RMP;
  pinAf(GPIOA, GPIO_PIN_9,  GPIO_AF1_USART1, GPIO_NOPULL);
  pinAf(GPIOA, GPIO_PIN_10, GPIO_AF1_USART1, GPIO_PULLUP);   // RO floats while this node transmits
  pinAf(GPIOB, GPIO_PIN_3,  GPIO_AF4_USART1, GPIO_NOPULL);   // USART1_DE (board has a 100 k pull-down)

  USART1->CR1 = 0;
  USART1->BRR = HAL_RCC_GetPCLK1Freq() / baud;
  USART1->CR3 = USART_CR3_DEM;                               // driver enable, active high
  USART1->CR1 = (8u << USART_CR1_DEAT_Pos) | (8u << USART_CR1_DEDT_Pos)   // 1/2 bit before / after
              | USART_CR1_RXNEIE_RXFNEIE | USART_CR1_TE | USART_CR1_RE;
  USART1->CR1 |= USART_CR1_UE;
  NVIC_SetPriority(USART1_IRQn, 1);
  NVIC_EnableIRQ(USART1_IRQn);
}

int  bus_read() { return busRx.pop(); }
void bus_write(const uint8_t *p, uint16_t n) { write(USART1, p, n); }

void dbg_init(uint32_t baud) {
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_USART2_CLK_ENABLE();
  pinAf(GPIOA, GPIO_PIN_2, GPIO_AF1_USART2, GPIO_NOPULL);
  pinAf(GPIOA, GPIO_PIN_3, GPIO_AF1_USART2, GPIO_PULLUP);    // pads may be unconnected
  USART2->CR1 = 0;
  USART2->BRR = HAL_RCC_GetPCLK1Freq() / baud;
  USART2->CR3 = 0;
  USART2->CR1 = USART_CR1_RXNEIE_RXFNEIE | USART_CR1_TE | USART_CR1_RE;
  USART2->CR1 |= USART_CR1_UE;
  NVIC_SetPriority(USART2_IRQn, 1);
  NVIC_EnableIRQ(USART2_IRQn);
}

int  dbg_read() { return dbgRx.pop(); }
void dbg_write(const uint8_t *p, uint16_t n) { write(USART2, p, n); }
