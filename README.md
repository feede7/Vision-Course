# Vision-Course

## Dependencies

```
sudo apt install ghdl gtkwave
pip3 install cocotb
```

## Using sources from FPGA Vision Course

https://github.com/Marco-Winzker/FPGA-Vision

```
git submodule init
git submodule update
```

## Run a lane_sobel test

```
cd CocoTest/test/lane_sobel
make
```

Or with pipeline cleaning

```
rm -r results.xml sim_build/ __pycache__/; make
```

## Watch the Waveforms

```
gtkwave waveform_sobel.vcd
```