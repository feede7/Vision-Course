import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge


CLK_PERIOD = 10  # ns


async def Reset(dut):
    dut.reset.value = 1
    dut.de_in.value = 0
    dut.data_in.value = 0
    await Timer(CLK_PERIOD * 10, units='ns')
    dut.reset.value = 0
    await Timer(CLK_PERIOD * 10, units='ns')
    await RisingEdge(dut.clk)


@cocotb.test()
async def init_test(dut):
    cocotb.fork(Clock(dut.clk, period=CLK_PERIOD, units='ns').start())
    await Reset(dut)

    for _ in range(1000):
        await RisingEdge(dut.clk)
