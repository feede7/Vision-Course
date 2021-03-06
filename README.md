# Vision-Course

## Testbench

### Dependencies

```
sudo apt install ghdl gtkwave
pip3 install cocotb pillow numpy opencv-python
```

### Using sources from FPGA Vision Course

https://github.com/Marco-Winzker/FPGA-Vision

```
git submodule init
git submodule update
```

### Run a lane_sobel test

```
cd CocoTest/test/lane_sobel
make
```

Or with pipeline cleaning

```
rm -r results.xml sim_build/ __pycache__/ waveform_sobel.vcd; make
```

This command will test the 3 images in `FPGA-Vision/Test_Images`
and will post the output images in `CocoTest/test`. It takes around
of 3 minutes by image.

### Watch the Waveforms

```
gtkwave waveform_sobel.vcd
```

## Bitfile generation

### Dependencies

```
sudo apt install hdlmake
```

### Install Quartus

```
git clone https://github.com/CTSRD-CHERI/quartus-install.git
cd quartus-install
sudo python3 quartus-install.py 18.1lite /opt/intelFPGA_lite/18.1 c4 c5 --prune --fix-libpng
```

### Using hdlmake

```
export PATH=${PATH}:/opt/intelFPGA_lite/18.1/quartus/bin
cd CocoTest/project/lane_sobel/C4
hdlmake
make
```

To ensure cleaning process, it's recomended to do this everytime you
change something

```
rm Makefile; hdlmake && make clean && make
```

### Build Dockerfile to CI

```
docker build -t quartus-lite .
docker tag quartus-lite:latest feede7/quartus-lite:latest
docker login
docker push feede7/quartus-lite:latest
```

## Run into Docker!

This point is to run everything with Docker!

```
docker run -v $(pwd):/root/mounted -w /root/mounted -it quartus-lite:latest /bin/bash
```
