#!/bin/bash
# You can call this script in CI to set up all Lummao dependencies during CI.
# After this you just need to `python setup.py install` and then you can use
# test scripts that `import lummao`.
pushd "$( dirname "${BASH_SOURCE[0]}" )"

sudo apt-get install cmake build-essential g++ flex bison

# Build and install tailslide
git clone https://github.com/SaladDais/tailslide tailslide
pushd tailslide
mkdir build
pushd build
cmake ..
sudo make -j2 install
popd
popd

# Build and install lummao binary components
mkdir build
pushd build
cmake ..
sudo make install
popd

# Download and install LSL-PyOptimizer
git clone https://github.com/Sei-Lisa/LSL-PyOptimizer.git pyoptimizer
export "LSL_PYOPTIMIZER_PATH=$(pwd)/pyoptimizer"

popd
