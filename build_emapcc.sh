#!/bin/bash
set -e
cd emap/emapcc
mkdir -p build
cd build
cmake .. && make