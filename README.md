# Vision-Course

## Dependencies

```
sudo apt install ghdl gtkwave
pip3 install cocotb pillow numpy opencv-python
```

## Using sources from FPGA Vision Course

https://github.com/Marco-Winzker/FPGA-Vision

```
git submodule init
git submodule update
```

## Possible improvement

Now this repo is thought for cloning it into `$HOME/Documents`

## Run a lane_sobel test

```
cd CocoTest/test/lane_sobel
make
```

Or with pipeline cleaning

```
rm -r results.xml sim_build/ __pycache__/; time make
```

This command will test the 3 images in `FPGA-Vision/Test_Images`
and will post the output images in `CocoTest/test`. It takes around
of 3 minutes by image.

## Watch the Waveforms

```
gtkwave waveform_sobel.vcd
```
