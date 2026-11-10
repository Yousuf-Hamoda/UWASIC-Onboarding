# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import ClockCycles
from cocotb.types import Logic
from cocotb.types import LogicArray

async def await_half_sclk(dut):
    """Wait for the SCLK signal to go high or low."""
    start_time = cocotb.utils.get_sim_time(units="ns")
    while True:
        await ClockCycles(dut.clk, 1)
        # Wait for half of the SCLK period (10 us)
        if (start_time + 100*100*0.5) < cocotb.utils.get_sim_time(units="ns"):
            break
    return

def ui_in_logicarray(ncs, bit, sclk):
    """Setup the ui_in value as a LogicArray."""
    return LogicArray(f"00000{ncs}{bit}{sclk}")

async def send_spi_transaction(dut, r_w, address, data):
    """
    Send an SPI transaction with format:
    - 1 bit for Read/Write
    - 7 bits for address
    - 8 bits for data
    
    Parameters:
    - r_w: boolean, True for write, False for read
    - address: int, 7-bit address (0-127)
    - data: LogicArray or int, 8-bit data
    """
    # Convert data to int if it's a LogicArray
    if isinstance(data, LogicArray):
        data_int = int(data)
    else:
        data_int = data
    # Validate inputs
    if address < 0 or address > 127:
        raise ValueError("Address must be 7-bit (0-127)")
    if data_int < 0 or data_int > 255:
        raise ValueError("Data must be 8-bit (0-255)")
    # Combine RW and address into first byte
    first_byte = (int(r_w) << 7) | address
    # Start transaction - pull CS low
    sclk = 0
    ncs = 0
    bit = 0
    # Set initial state with CS low
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 1)
    # Send first byte (RW + Address)
    for i in range(8):
        bit = (first_byte >> (7-i)) & 0x1
        # SCLK low, set COPI
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # SCLK high, keep COPI
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # Send second byte (Data)
    for i in range(8):
        bit = (data_int >> (7-i)) & 0x1
        # SCLK low, set COPI
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # SCLK high, keep COPI
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # End transaction - return CS high
    sclk = 0
    ncs = 1
    bit = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 600)
    return ui_in_logicarray(ncs, bit, sclk)

@cocotb.test()
async def test_spi(dut):
    dut._log.info("Start SPI test")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    dut._log.info("Test project behavior")
    dut._log.info("Write transaction, address 0x00, data 0xF0")
    ui_in_val = await send_spi_transaction(dut, 1, 0x00, 0xF0)  # Write transaction
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 1000) 

    dut._log.info("Write transaction, address 0x01, data 0xCC")
    ui_in_val = await send_spi_transaction(dut, 1, 0x01, 0xCC)  # Write transaction
    assert dut.uio_out.value == 0xCC, f"Expected 0xCC, got {dut.uio_out.value}"
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x30 (invalid), data 0xAA")
    ui_in_val = await send_spi_transaction(dut, 1, 0x30, 0xAA)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Read transaction (invalid), address 0x00, data 0xBE")
    ui_in_val = await send_spi_transaction(dut, 0, 0x30, 0xBE)
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 100)
    
    dut._log.info("Read transaction (invalid), address 0x41 (invalid), data 0xEF")
    ui_in_val = await send_spi_transaction(dut, 0, 0x41, 0xEF)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x02, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x02, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x04, data 0xCF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xCF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x00")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x00)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x01")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x01)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("SPI test completed successfully")

# ---------------------------------------------------------------------------
# PWM tests
# ---------------------------------------------------------------------------

CLK_PERIOD_NS = 100                  # 10 MHz clock
PWM_PERIOD_CLKS = 13 * 256           # (clk_div_trig + 1) * 256 -> ~3004.8 Hz
TIMEOUT_CLKS = 3 * PWM_PERIOD_CLKS   # 0x00 / 0xFF never toggle


# Start the clock and reset with the SPI bus idle.
async def reset_dut(dut):
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD_NS, units="ns").start())
    dut.ena.value = 1
    dut.ui_in.value = ui_in_logicarray(1, 0, 0)   # nCS high
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)


# Enable PWM on uo_out[0] and uio_out[0] with the given duty cycle.
async def setup_pwm(dut, duty):
    await send_spi_transaction(dut, 1, 0x00, 0x01)   # output enable
    await send_spi_transaction(dut, 1, 0x01, 0x01)
    await send_spi_transaction(dut, 1, 0x02, 0x01)   # PWM mode
    await send_spi_transaction(dut, 1, 0x03, 0x01)
    await send_spi_transaction(dut, 1, 0x04, duty)


# Output pin 0-15 of {uio_out, uo_out}.
def get_bit(dut, pin):
    bus = int(dut.uo_out.value) if pin < 8 else int(dut.uio_out.value)
    return (bus >> (pin % 8)) & 1


# Poll each clk until the pin equals `level`. Returns sim time (ns) or None.
async def wait_for_level(dut, pin, level, timeout_clks=TIMEOUT_CLKS):
    for _ in range(timeout_clks):
        await RisingEdge(dut.clk)
        if get_bit(dut, pin) == level:
            return cocotb.utils.get_sim_time(units="ns")
    return None


# Time of the next rising/falling edge (ns), or None on timeout.
async def wait_for_edge(dut, pin, rising, timeout_clks=TIMEOUT_CLKS):
    before, after = (0, 1) if rising else (1, 0)
    # reach the opposite level first so an already-high pin isn't a rising edge
    if await wait_for_level(dut, pin, before, timeout_clks) is None:
        return None
    return await wait_for_level(dut, pin, after, timeout_clks)


# Returns (period_ns, high_ns) for one cycle, or None if the pin doesn't toggle.
async def measure_pwm(dut, pin):
    t1 = await wait_for_edge(dut, pin, rising=True)
    tf = await wait_for_edge(dut, pin, rising=False) if t1 is not None else None
    t2 = await wait_for_edge(dut, pin, rising=True) if tf is not None else None
    if t2 is None:
        return None
    return (t2 - t1, tf - t1)


# 3 kHz +/- 1% on both output banks.
@cocotb.test()
async def test_pwm_freq(dut):
    await reset_dut(dut)
    for duty in [0x01, 0x40, 0x80, 0xFE]:
        await setup_pwm(dut, duty)
        for pin in [0, 8]:                           # uo_out[0], uio_out[0]
            result = await measure_pwm(dut, pin)
            assert result is not None, f"duty 0x{duty:02X}, pin {pin}: no PWM edges"
            period_ns, _ = result
            freq_hz = 1e9 / period_ns
            dut._log.info(f"duty 0x{duty:02X}, pin {pin}: {freq_hz:.1f} Hz")
            assert 2970 <= freq_hz <= 3030, f"frequency {freq_hz:.1f} Hz out of range"
    dut._log.info("PWM Frequency test completed successfully")


# Duty = value/256 +/- 1%; 0x00 always low, 0xFF always high.
@cocotb.test()
async def test_pwm_duty(dut):
    await reset_dut(dut)
    for duty in [0x00, 0x01, 0x40, 0x80, 0xC0, 0xFE, 0xFF]:
        await setup_pwm(dut, duty)
        result = await measure_pwm(dut, 0)
        if duty == 0x00:
            assert result is None and get_bit(dut, 0) == 0, "0x00 should stay low"
            dut._log.info("duty 0x00: stays low")
        elif duty == 0xFF:
            assert result is None and get_bit(dut, 0) == 1, "0xFF should stay high"
            dut._log.info("duty 0xFF: stays high")
        else:
            assert result is not None, f"duty 0x{duty:02X}: no PWM edges"
            period_ns, high_ns = result
            measured = 100.0 * high_ns / period_ns
            expected = 100.0 * duty / 256
            dut._log.info(f"duty 0x{duty:02X}: measured {measured:.2f}%, expected {expected:.2f}%")
            assert abs(measured - expected) <= 1.0, f"duty 0x{duty:02X} off by more than 1%"
    dut._log.info("PWM Duty Cycle test completed successfully")


# Output enable takes precedence over PWM mode.
@cocotb.test()
async def test_enable_interaction(dut):
    await reset_dut(dut)
    await send_spi_transaction(dut, 1, 0x04, 0x80)

    # en=0, pwm=1 -> 0
    await send_spi_transaction(dut, 1, 0x02, 0x01)
    await send_spi_transaction(dut, 1, 0x00, 0x00)
    assert await measure_pwm(dut, 0) is None and get_bit(dut, 0) == 0, "en=0, pwm=1 should be 0"

    # en=1, pwm=0 -> 1
    await send_spi_transaction(dut, 1, 0x02, 0x00)
    await send_spi_transaction(dut, 1, 0x00, 0x01)
    assert await measure_pwm(dut, 0) is None and get_bit(dut, 0) == 1, "en=1, pwm=0 should be 1"

    # en=1, pwm=1 -> PWM
    await send_spi_transaction(dut, 1, 0x02, 0x01)
    assert await measure_pwm(dut, 0) is not None, "en=1, pwm=1 should toggle"
    dut._log.info("Enable/PWM interaction test completed successfully")
