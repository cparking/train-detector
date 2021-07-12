from ubuntu:18.04

# Install prerequisites
run apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    cmake \
    curl \
    git \
    libcurl3-dev \
    libleptonica-dev \
    liblog4cplus-dev \
    libopencv-dev \
    libtesseract-dev \
    nano \    
    wget \
    python3.8 \
    python3-pip

RUN python3 -m pip install Pillow
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install opencv-python==4.0.0.21
RUN python3 -m pip install pyyaml

# Copy all data
copy . /srv/openalpr

# Setup the build directory
run mkdir /srv/openalpr/src/build
workdir /srv/openalpr/src/build

# Setup the compile environment
run cmake -DCMAKE_INSTALL_PREFIX:PATH=/usr -DCMAKE_INSTALL_SYSCONFDIR:PATH=/etc -DWITH_UTILITIES=OFF -DWITH_DAEMON=OFF -DWITH_TESTS=OFF .. && \
    make -j2 && \
    make install

workdir /srv/openalpr/train-detector-master

