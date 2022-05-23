import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge
from cocotb.regression import TestFactory as TF
from os import environ
from PIL import Image
import numpy as np

HOME = environ['HOME']
REPO_PATH = HOME + '/Documents/Vision-Course'
IMG_PATH = REPO_PATH + '/FPGA-Vision/Test_Images/'
OUT_PATH = REPO_PATH + '/CocoTest/test/lane_sobel/'

CLK_PERIOD = 10  # ns

async def Reset(dut):
    dut.reset.value = 1
    dut.de_in.value = 0
    dut.data_in.value = 0
    await Timer(CLK_PERIOD * 10, units='ns')
    dut.reset.value = 0
    await Timer(CLK_PERIOD * 10, units='ns')
    await RisingEdge(dut.clk)

async def send_image(dut, flat_image):
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.de_in.value = 1
    for pixel in flat_image:
        dut.data_in.value = int(pixel)
        await RisingEdge(dut.clk)
    
    dut.de_in.value = 0
    await RisingEdge(dut.clk)

async def test_filter(dut, filter_name, img_name):
    cocotb.fork(Clock(dut.clk, period=CLK_PERIOD, units='ns').start())
    await Reset(dut)

    CORE_LATENCY = 10

    test_image = IMG_PATH + img_name
    image = np.array(Image.open(test_image), dtype=np.uint8)
    height, width, _ = image.shape

    flat_image = list(range(height*width))
    for i in range(height):
        for j in range(width):
            pixel = image[i, j, :]
            flat_image[i*width+j] = (pixel[2] << 16) + (pixel[1] << 8) + pixel[0]

    cocotb.fork(send_image(dut, flat_image))

    await RisingEdge(dut.de_in)

    for _ in range(CORE_LATENCY):
        await RisingEdge(dut.clk)

    for i in range(height):
        for j in range(width):
            data_out = dut.data_out.value
            for k in range(3):
                image[i, j, k] = (data_out >> ((2-k)*8)) & 0xFF
            await RisingEdge(dut.clk)

    await RisingEdge(dut.clk)

    assert dut.de_in.value == 0

    await RisingEdge(dut.clk)

    im = Image.fromarray(image)
    im.save(OUT_PATH + img_name.replace('.bmp', f'_{filter_name}_out.bmp'))
    

tf_sobel = TF(test_filter)
tf_sobel.add_option('filter_name', ['sobel'])
tf_sobel.add_option('img_name', [f'street_{n}.bmp' for n in ['A', 'B', 'C']])
tf_sobel.generate_tests()
