FROM debian:buster-slim

RUN apt-get update && apt-get install -y aria2 make git python python3

WORKDIR /root

RUN git clone --depth 1 https://github.com/dcaruso/quartus-install.git

RUN quartus-install/quartus-install.py 18.1lite /opt/intelFPGA_lite/18.1 c4 c5 --prune
RUN cd /opt/intelFPGA_lite/18.1/ && rm -rf logs \
            hls \
            nios2eds \
            uninstall \
            quartus/eda \
            quartus/linux64/jre64 \
            ip

RUN cd /opt/intelFPGA_lite/18.1/quartus/common/devinfo/programmer/ && rm -fv !"(ep2agx*|*ep2agx*|*ep2agx|mt25qu128*|pgm_dev_info.pcf|pgm_flash.pcf)"

# Solution from: https://forums.intel.com/s/question/0D50P00003yyTA4SAM/quartus-failed-to-run-inside-docker-linux?language=en_US
RUN cd /opt/intelFPGA_lite/18.1/quartus/linux64/ && rm libstdc++.so.6  && ln -s /usr/lib/x86_64-linux-gnu/libstdc++.so.6 libstdc++.so.6

RUN rm -rf quartus-install

RUN apt-get install -y libglib2.0-0

ENV LC_CTYPE=C
ENV LC_NUMERIC=en_US.UTF-8
