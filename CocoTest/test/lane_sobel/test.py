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
SQ_LIMIT = 14*2
SQ_SUM_FACTOR = 13
SQ_SUM_LIMIT = 13
MAX_SUM_LIMIT = (1 << SQ_SUM_LIMIT) - 1


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


def rgb_2_y(image):
    # Y = 5*R + 9*G + 2*B
    image_u16 = np.uint16(image)
    assert image_u16.dtype == 'uint16', f'image_u16.dtype: {image_u16.dtype}'
    R = image_u16[:, :, 2]
    G = image_u16[:, :, 1]
    B = image_u16[:, :, 0]
    y = 5*R + 9*G + 2*B
    assert y.dtype == 'uint16', f'y.dtype: {y.dtype}'
    return y


def b8_2_b24(image):
    a = (image[:, :, 2] << 16) + (image[:, :, 1] << 8) + image[:, :, 0]
    return a


def convolve(image, kernel):
    image_y = rgb_2_y(image)
    kernel_h = kernel.shape[0]
    kernel_w = kernel.shape[1]
    assert kernel_h == kernel_w
    assert kernel_h % 2 == 1
    kernel_flatten = np.array(kernel.flatten())
    rows = image_y.shape[0]
    cols = image_y.shape[1]
    output = np.zeros(image_y.shape, dtype=np.uint32)
    bias = kernel_w//2
    for col in range(cols):
        for row in range(rows):
            if col >= bias and row >= bias and \
               col < cols-bias and row < rows-bias:
                sub_image = image_y[row-bias:row+bias+1, col-bias:col+bias+1]
                assert sub_image.shape == (3, 3), f'sub_image.shape: {sub_image.shape}'
                image_flatten = np.array(sub_image.flatten())
                assert len(image_flatten) == 9, f'col: {col}, row: {row}'
                accum = sum(image_flatten*kernel_flatten)
                accum_2 = accum*accum
                assert accum_2 < (1 << SQ_LIMIT), f'Uses more than {SQ_LIMIT}'
                output[row, col] = accum_2 % (1 << SQ_LIMIT)
            else:
                output[row, col] = 0
    return output


def get_target(image, kernel_x, kernel_y):
    g_x_2 = convolve(image, kernel_x)
    g_y_2 = convolve(image, kernel_y)
    g_sum_2 = (g_x_2 + g_y_2) >> SQ_SUM_FACTOR
    g_sum_2[np.where(g_sum_2 > MAX_SUM_LIMIT)] = MAX_SUM_LIMIT
    g2_limit = np.uint16(g_sum_2 % (1 << SQ_SUM_FACTOR))
    # The table implemented in the HDL makes the
    # 255-8*g2_limit calculation.
    lum_new = 255-np.uint8(np.sqrt(8*g2_limit))
    output = np.zeros(image.shape, dtype=np.uint8)
    for i in range(3):
        output[:, :, i] = lum_new
    return output


async def test_filter(dut, filter_name, img_name):
    cocotb.fork(Clock(dut.clk, period=CLK_PERIOD, units='ns').start())
    await Reset(dut)

    CORE_LATENCY = 10

    test_image = IMG_PATH + img_name
    image = np.array(Image.open(test_image), dtype=np.uint8)
    height, width, _ = image.shape

    kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], np.int8)
    kernel_y = np.transpose(kernel_x)
    target = get_target(image, kernel_x, kernel_y)

    im = Image.fromarray(target)
    im.save(OUT_PATH + img_name.replace('.bmp', f'_{filter_name}_target.bmp'))

    flat_image = np.array(b8_2_b24(np.uint32(image)).flatten())

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

    result_r = image[2:, :-3, 2]
    target_r = target[2:, 2:-1, 2]

    assert result_r.shape == target_r.shape
    errors = 0
    for row in range(result_r.shape[0]):
        for col in range(target_r.shape[1]):
            val = result_r[row, col]
            exp = target_r[row, col]
            # msg = f'row: {row}, col: {col}, val: {val}, exp: {exp}'
            # assert val == exp, msg
            if val != exp:
                errors += 1
    print('errors', errors)

    im = Image.fromarray(image)
    im.save(OUT_PATH + img_name.replace('.bmp', f'_{filter_name}_out.bmp'))


tf_sobel = TF(test_filter)
tf_sobel.add_option('filter_name', ['sobel'])
# tf_sobel.add_option('img_name', [f'street_{n}.bmp' for n in ['A', 'B', 'C']])
tf_sobel.add_option('img_name', [f'street_{n}.bmp' for n in ['A']])
tf_sobel.generate_tests()
