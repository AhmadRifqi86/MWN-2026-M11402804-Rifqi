# ns-3 lab image — build once, reuse forever.
# ns-3 itself is NOT baked in; it is cloned into a mounted volume so your
# source and results live on the host (editable + git-friendly).
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# ns-3 build toolchain + packet-analysis tools + python plotting stack.
# The debconf line stops tshark from opening an interactive prompt during build.
RUN echo "wireshark-common wireshark-common/install-setuid boolean false" | debconf-set-selections \
 && apt-get update && apt-get install -y --no-install-recommends \
      g++ gcc make cmake ninja-build \
      python3 python3-dev \
      git ca-certificates \
      tshark tcpdump \
      python3-numpy python3-pandas python3-matplotlib \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /work
CMD ["/bin/bash"]
