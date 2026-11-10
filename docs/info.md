<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

An SPI (mode 0, write-only) is used to communicate with the PWM. It sets five 8-bit registers which control 16 outputs, each of which can be off, static high, or 3khz PWM with a programmable cycle. 

## How to test

Send 16-bit SPI frames (mode 0) on ui_in[0] (SCLK), ui_in[1] (COPI) and ui_in[2] (nCS):
1 bit R/W (1 = write), 7-bit address, 8-bit data, MSB first.

- Write 0xFF to 0x00: all of uo_out goes high.
- Write 0x01 to 0x02 and 0x80 to 0x04: uo_out[0] outputs a 3 kHz, 50% PWM signal.

The cocotb tests in test/test.py cover register writes, PWM frequency, duty cycle, and the output-enable / PWM-mode interaction.

## External hardware

An SPI controller, such as a microcontroller, to write the registers. Optionally LEDs or a scope on the outputs to see the PWM.