/*
 * demo_driver.c —— STM32 外设初始化示例(用于演示代码索引)
 * 含 GPIO / SPI / UART 初始化,带寄存器操作注释,适合检索
 */
#include "stm32f4xx.h"

/* GPIOA 初始化:PA0 配推挽输出,PA1 配复用功能(SPI1 SCK)*/
void gpio_init(void)
{
    /* 使能 GPIOA 时钟:RCC AHB1ENR 的 bit0(GPIOAEN)*/
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;

    /* PA0:输出模式。MODER 的 bit[1:0] = 01(通用输出)*/
    GPIOA->MODER &= ~(3 << 0);
    GPIOA->MODER |= (1 << 0);

    /* PA0:推挽输出。OTYPER bit0 = 0(推挽)*/
    GPIOA->OTYPER &= ~(1 << 0);

    /* PA1:复用功能。MODER bit[3:2] = 10(复用)*/
    GPIOA->MODER &= ~(3 << 2);
    GPIOA->MODER |= (2 << 2);
}

/* SPI1 初始化:主机模式,8 位数据,波特率 FPCLK/16 */
void spi_init(void)
{
    /* 使能 SPI1 时钟:RCC APB2ENR 的 bit12(SPI1EN)*/
    RCC->APB2ENR |= RCC_APB2ENR_SPI1EN;

    SPI1->CR1 = 0;

    /* CR1:主机(MSTR bit2)、波特率 BR=101(FPCLK/16,bit5:3)、软件片选 SSM bit9 */
    SPI1->CR1 = SPI_CR1_MSTR | SPI_CR1_BR_2 | SPI_CR1_BR_0 | SPI_CR1_SSM | SPI_CR1_SSI;

    /* 使能 SPI:CR1 的 bit6(SPE)*/
    SPI1->CR1 |= SPI_CR1_SPE;
}

/* USART2 初始化:115200 波特率,8N1 */
void uart_init(void)
{
    /* 使能 USART2 时钟:RCC APB1ENR bit17(USART2EN)*/
    RCC->APB1ENR |= RCC_APB1ENR_USART2EN;

    /* 波特率 115200:BRR 写分频值 */
    USART2->BRR = (84000000 / 16) / 115200;

    /* CR1:使能发送(TE bit3)、使能 USART(UE bit13)*/
    USART2->CR1 = USART_CR1_TE | USART_CR1_UE;
}

/* 简单延时(ms 级,粗略)*/
void delay_ms(unsigned int ms)
{
    volatile unsigned int i, j;
    for (i = 0; i < ms; i++)
        for (j = 0; j < 10000; j++)
            ;
}

int main(void)
{
    gpio_init();
    spi_init();
    uart_init();

    while (1) {
        GPIOA->ODR ^= (1 << 0);   /* 翻转 PA0,LED 闪烁 */
        delay_ms(500);
    }
}
