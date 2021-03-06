FROM debian:stretch-slim

RUN apt-get update && apt-get install -y aria2 make git python python3 libglib2.0-0

WORKDIR /root

RUN git clone --depth 1 https://github.com/CTSRD-CHERI/quartus-install.git

ENV QUARTUS_VERSION=18.1
ENV LITE_FLAG=lite

RUN quartus-install/quartus-install.py ${QUARTUS_VERSION}${LITE_FLAG} /opt/intelFPGA_lite/${QUARTUS_VERSION} c4 c5 --prune
RUN cd /opt/intelFPGA_lite/${QUARTUS_VERSION}/ && rm -rf logs \
            hls \
            nios2eds \
            uninstall \
            quartus/eda \
            quartus/linux64/jre64 \
            ip

RUN cd /opt/intelFPGA_lite/${QUARTUS_VERSION}/quartus/common/devinfo/programmer/ && rm -fv !"(ep2agx*|*ep2agx*|*ep2agx|mt25qu128*|pgm_dev_info.pcf|pgm_flash.pcf)"

# Solution from: https://forums.intel.com/s/question/0D50P00003yyTA4SAM/quartus-failed-to-run-inside-docker-linux?language=en_US
RUN cd /opt/intelFPGA_lite/${QUARTUS_VERSION}/quartus/linux64/ && rm libstdc++.so.6  && ln -s /usr/lib/x86_64-linux-gnu/libstdc++.so.6 libstdc++.so.6

RUN rm -rf quartus-install

# Solution from: https://community.intel.com/t5/Intel-Quartus-Prime-Software/Quartus-failed-to-run-inside-Docker-Linux/m-p/241059/highlight/true#M54719
RUN apt-get install libtcmalloc-minimal4
ENV LD_PRELOAD=/usr/lib/libtcmalloc_minimal.so.4

ENV PATH=$PATH:/opt/intelFPGA_lite/${QUARTUS_VERSION}/quartus/bin
