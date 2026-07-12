# GPIO 寄存器

GPIOA 的各寄存器用于配置引脚的模式、输出类型、速度等。

## MODER 寄存器

GPIOA MODER 配置引脚模式,每位 2 bit:00=输入,01=输出,10=复用,11=模拟。
PA0 占 bit[1:0],PA1 占 bit[3:2],依次类推。

## OTYPER 寄存器

GPIOA OTYPER 配置输出类型,每位 1 bit:0=推挽,1=开漏。

# USART 寄存器

USART2 用于串口通信,各寄存器配置波特率、数据格式、中断等。

## BRR 寄存器

USART2 BRR 配置波特率,写入分频值,波特率 = APB 时钟 / BRR。

## CR1 寄存器

USART2 CR1 使能发送(TE)、接收(RE)和 USART 本身(UE)。
