# Static BusyBox for Anyka AK3918 (ARM926EJ-S / ARMv5TEJ, EABI5 soft-float).
# debian bookworm = live mirrors; gcc-arm-linux-gnueabi = Debian "armel" =
# ARMv5TE little-endian soft-float, ARM mode (no Thumb-2) = exactly this core.
# glibc static binaries only need Linux >= 3.2, so they run on the cam's 4.4.
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc-arm-linux-gnueabi libc6-dev-armel-cross \
        build-essential make bc bzip2 wget ca-certificates file xz-utils qemu-user \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY build.sh /build/build.sh
RUN chmod +x /build/build.sh
ENTRYPOINT ["/build/build.sh"]
