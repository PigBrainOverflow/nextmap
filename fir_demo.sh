#!/bin/bash

# Simple FIR Demo Script - DSP Technology Mapping
# Run this from the project root directory

export PATH="$HOME/Documents/tools/yosys:$PATH"

echo "=== FIR Filter Nextmap Demo ==="
echo

# Create output directory
mkdir -p eval/out

echo "Running DSP optimization on fir_n16_w8 design..."
echo

yosys -m ./nextmap_plugin_simple.so -p "
    read_verilog eval/fir/fir_n16_w8.v
    proc; opt_merge; opt_clean
    log '=== BEFORE NEXTMAP DSP OPTIMIZATION ==='
    stat
    nextmap -strategy dsp
    log '=== AFTER NEXTMAP DSP OPTIMIZATION ==='
    stat
    write_verilog eval/out/fir_n16_w8_nextmap.v
"

echo
echo "=== Demo Complete ==="
echo "Key results to look for:"
echo "  - 'Applied X total rewrites'"
echo "  - 'Removed X dominated cells'"
echo "  - Before: ~80 cells (16 \$add, 32 \$dff, 16 \$mul, 16 \$mux)"
echo "  - After: ~59 cells (15 \$dff, 15 \$mux, 29 dsp_generic)"
echo
echo "Optimized design saved to: eval/out/fir_n16_w8_nextmap.v"
