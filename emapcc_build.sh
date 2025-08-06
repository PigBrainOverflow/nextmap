#!bin/bash

cd emap/cpp
mkdir -p build
cd build
cmake ..
make -j$(nproc)