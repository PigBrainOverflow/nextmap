#!/bin/bash

# Demo runner script for nextmap Yosys plugin
export PATH="$HOME/Documents/tools/yosys:$PATH"

echo "=== Nextmap Yosys Plugin Demo ==="
echo

# Test 1: Basic strategy with simple adder
echo "1. Testing basic strategy with test_adder.v"
yosys -m ./nextmap_plugin_simple.so -p "read_verilog test_adder.v; prep; stat; nextmap; stat" -q

echo
echo "2. Testing retiming strategy (requires tests/bad_multiplier.v)"
if [ -f "tests/bad_multiplier.v" ]; then
    yosys -m ./nextmap_plugin_simple.so -s scripts/retiming_demo.ys -q
else
    echo "Skipping retiming demo - tests/bad_multiplier.v not found"
fi

echo
echo "3. Testing comprehensive strategy"
yosys -m ./nextmap_plugin_simple.so -p "read_verilog test_adder.v; prep; nextmap -strategy comprehensive; stat" -q

echo
echo "4. Testing help command"
yosys -m ./nextmap_plugin_simple.so -p "help nextmap" -q

echo
echo "=== Demo Complete ==="