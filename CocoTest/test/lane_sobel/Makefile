# sudo apt install ghdl
# git clone https://github.com/CTSRD-CHERI/quartus-install.git
# sudo apt install aria2
# sudo python3 quartus-install.py 21.1pro /opt/intelFPGA/21.1pro c4 c5

VHDL_SOURCES = $(CURDIR)/../../../FPGA-Vision/FPGA-Design/lane_sobel.vhd \
			   $(CURDIR)/../../../FPGA-Vision/FPGA-Design/lane_linemem.vhd \
			   $(CURDIR)/../../../FPGA-Vision/FPGA-Design/lane_g_matrix.vhd \
			   $(CURDIR)/../../src/lane_g_root_IP.vhd

export PYTHONPATH := ../../:./:$(PYTHONPATH)

TOPLEVEL=lane_sobel
MODULE=test
SIM_ARGS+=--vcd=waveform_sobel.vcd
SIM=ghdl

include $(shell cocotb-config --makefiles)/Makefile.sim

