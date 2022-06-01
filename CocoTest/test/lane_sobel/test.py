from cocotb import fork
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge
from cocotb.regression import TestFactory as TF
from os import environ, path
from PIL import Image
import numpy as np
from cv2 import getDerivKernels

HOME = environ['HOME']
REPO_PATH = '../../..'
IMG_PATH = path.join(REPO_PATH, 'FPGA-Vision/Test_Images')
OUT_PATH = path.join(REPO_PATH, 'CocoTest/test/lane_sobel')

CLK_PERIOD = 10  # ns
SQ_LIMIT = 14*2
SQ_SUM_FACTOR = 13
SQ_SUM_LIMIT = 18
MAX_SUM_LIMIT = (1 << SQ_SUM_FACTOR) - 1


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


def get_target(image, kernel):
    kernel_y = kernel
    kernel_x = np.transpose(kernel_y)
    g_x_2 = convolve(image, kernel_x)
    g_y_2 = convolve(image, kernel_y)
    g_sum_2 = (g_x_2 + g_y_2) >> SQ_SUM_FACTOR
    g2_limit = np.zeros(g_sum_2.shape, dtype=np.uint32)
    g2_limit[:, :] = g_sum_2[:, :]
    g2_limit[np.where(g2_limit > MAX_SUM_LIMIT)] = MAX_SUM_LIMIT
    g2_limit = g2_limit % (1 << SQ_SUM_LIMIT)
    # The table implemented in the HDL makes the
    # 255-8*g2_limit calculation.
    lum_new = 255-np.uint8(np.sqrt(8*g2_limit))
    output = np.zeros(image.shape, dtype=np.uint8)
    for i in range(3):
        output[:, :, i] = lum_new
    return (output, g2_limit, g_sum_2, g_x_2, g_y_2)


async def collect_data(clk, signal, height, width,
                       dtype=np.uint32):
    mask = (1 << len(signal)) - 1
    output = np.zeros((height, width), dtype=dtype)
    for i in range(height):
        for j in range(width):
            output[i, j] = signal.value & mask
            await RisingEdge(clk)
    return output


def validate_matrix(kernel_width, a, b, LINE_DELAY=1):
    # This validation take account of the dirty margins
    assert a.shape == b.shape
    offset = kernel_width//2
    if len(a.shape) == 2:
        a1 = a[offset+LINE_DELAY:, offset+LINE_DELAY:]
        b1 = b[offset:-LINE_DELAY, offset:-LINE_DELAY]
    elif len(a.shape) == 3:
        a1 = a[offset+LINE_DELAY:, offset+LINE_DELAY:, :]
        b1 = b[offset:-LINE_DELAY, offset:-LINE_DELAY, :]
    assert (a1 == b1).all()


def get_kernel(filter):
    assert filter in ['sobel', ]
    if filter == 'sobel':
        sobel3x = getDerivKernels(1, 0,  3)
        kernel = np.int8(np.outer(sobel3x[0], sobel3x[1]))
    return kernel


async def test_filter(dut, filter_name, img_name):
    fork(Clock(dut.clk, period=CLK_PERIOD, units='ns').start())
    await Reset(dut)

    CORE_LATENCY = 7

    test_image = path.join(IMG_PATH, img_name)
    image = np.array(Image.open(test_image), dtype=np.uint8)
    height, width, _ = image.shape

    kernel = get_kernel(filter_name)
    output_target, g2_limit_target, \
    g_sum_2_target, g_x_2_target, \
    g_y_2_target = get_target(image, kernel)

    im = Image.fromarray(output_target)
    im.save(OUT_PATH + img_name.replace('.bmp', f'_{filter_name}_target.bmp'))

    flat_image = np.array(b8_2_b24(np.uint32(image)).flatten())

    fork(send_image(dut, flat_image))

    await RisingEdge(dut.de_in_r)

    for _ in range(CORE_LATENCY-3):
        await RisingEdge(dut.clk)

    g_x_2_fork = fork(collect_data(clk=dut.clk,
                                   signal=dut.g_x_2,
                                   height=height,
                                   width=width))

    g_y_2_fork = fork(collect_data(clk=dut.clk,
                                   signal=dut.g_y_2,
                                   height=height,
                                   width=width))
    await RisingEdge(dut.clk)

    g_sum_2_fork = fork(collect_data(clk=dut.clk,
                                     signal=dut.g_sum_2,
                                     height=height,
                                     width=width))
    await RisingEdge(dut.clk)

    g2_limit_fork = fork(collect_data(clk=dut.clk,
                                      signal=dut.g2_limit,
                                      height=height,
                                      width=width))
    await RisingEdge(dut.clk)

    output = np.zeros(image.shape, dtype=np.uint8)
    for i in range(height):
        for j in range(width):
            data_out = dut.data_out.value
            for k in range(3):
                output[i, j, k] = (data_out >> ((2-k)*8)) & 0xFF
            await RisingEdge(dut.clk)

    await RisingEdge(dut.clk)

    assert dut.de_in.value == 0

    await RisingEdge(dut.clk)

    # Debug of different stages
    g_x_2 = g_x_2_fork.retval
    g_y_2 = g_y_2_fork.retval
    g_sum_2 = g_sum_2_fork.retval
    g2_limit = g2_limit_fork.retval
    validate_matrix(kernel.shape[0], g_x_2, g_x_2_target)
    validate_matrix(kernel.shape[0], g_y_2, g_y_2_target)
    validate_matrix(kernel.shape[0], g_sum_2, g_sum_2_target)
    validate_matrix(kernel.shape[0], g2_limit, g2_limit_target)

    # Compare final results
    validate_matrix(kernel.shape[0], output, output_target)

    im = Image.fromarray(output)
    im.save(path.join(OUT_PATH,
                      img_name.replace('.bmp', f'_{filter_name}_out.bmp')))


tf_sobel = TF(test_filter)
tf_sobel.add_option('filter_name', ['sobel'])
tf_sobel.add_option('img_name', [f'street_{n}.bmp' for n in ['A', 'B', 'C']])
tf_sobel.generate_tests()
