## Evaluation

### Handcrafted
Results by plain cost model:

| Name | Description | Nextmap |        |    |                 | Yosys |        |    |                | Proprietary |       |    |                 |
|------|-------------|---------|--------|----|-----------------|-------|--------|----|----------------|-------|-------|----|-----------------|
|      |             | DSP     | CARRY4 | FF | Other Resources | DSP   | CARRY4 | FF | Other Resources | DSP   | CARRY4 | FF | Other Resources |
| bad_multiplier | 16-bit truncated multiplier | 1 | 0 | 0 | N.A. | 1 | 0 | 64 | N.A. | 1 | 0 | 0 | N.A. |
| complex_multiplier | $(a + bi) \times (c + di)$ | 3 | 0 | 64 | N.A. | 4 | 16 | 128 | LUT2: 64 | 4 | 0 | 64 | N.A. |
| dot_product | $a\times b + c\times d$ | 2 | 0 | 32 | N.A. | 2 | 8 | 64 | LUT2: 32 | 2 | 0 | 32 | N.A. |
| multiplier_with_rst | 16-bit multiplier with synchronous reset | 1 | 0 | 0 | N.A. | 1 | 0 | 64 | N.A. | 1 | 0 | 0 | N.A. |
| redundant_adders | Three adders with shared inputs but different widths | 0 | 8 | 0 | LUT2: 32 | 0 | 14 | 0 | LUT2: 32 | 0 | 14 | 0 | LUT2: 57 |
| signed_mac | $a \times b + c$ | 1 | 0 | 32 | N.A. | 1 | 8 | 64 | LUT2: 32 | 1 | 0 | 32 | N.A. |
| signed_reg | sign-extension and delay | 0 | 0 | 32 | N.A. | 0 | 0 | 32 | N.A. | 0 | 0 | 32 | N.A. |
| square_diff | $(a - b)^2$ | 1 | 0 | 64 | N.A. | 1 | 5 | 83 | LUT2: 16 | 1 | 5 | 32 | LUT2: 16 |
| unsigned_mac | $a \times b + c$ | 1 | 0 | 32 | N.A. | 1 | 8 | 64 | LUT2: 32 | 1 | 0 | 32 | N.A. |
| wide_multiplier | 16-32-bit multiplier | 2 | 0 | 17 | N.A. | 2 | 4 | 64 | LUT2: 15 | 2 | 0 | 17 | N.A. |

NOTE: Check bad_multiplier and wide_multiplier.

### Systolic Array
#### DSP

| Matrix Size | Weight Bitwidth | Nextmap |        |    |                 | Yosys |        |    |                 | Proprietary |        |    |                 |
|-------------|-----------------|---------|--------|----|-----------------|-------|--------|----|-----------------|-------|--------|----|-----------------|
|             |                 | DSP     | CARRY4 | FF | Other Resources | DSP   | CARRY4 | FF | Other Resources | DSP   | CARRY4 | FF | Other Resources |
| 4x4 | 8 | 16 | 0 | 0 | N.A. | 16 | 64 | 448 | LUTx: 400 | 0 | 256 | 448 | LUTx: 1648 |
| 4x4 | 16 | 16 | 0 | 0 | N.A. | 16 | 128 | 896 | LUTx: 864 | 16 | 0 | 16 | N.A. |
| 4x4 | 32 | 48 | 728 | 1928 | LUTx: 3024 | 64 | 720 | 1792 | LUTx: 3848 | 64 | 448 | 1280 | LUTx: 1776 |
| | | 53 | 614 | 1120 | LUTx: 4176 |
| 8x8 | 8 | 64 | 0 | 0 | N.A. | 64 | 256 | 1920 | LUTx: 1600 | 0 | 1024 | 1920 | LUTx: 6592 |
| 8x8 | 16 | 64 | 0 | 0 | N.A. | 64 | 512 | 3840 | LUTx: 3008 | 64 | 0 | 528 | N.A. |
| 8x8 | 32 | 192 | 2787 | 8649 | LUTx: 11696 | 256 | 2880 | 7680 | LUTx: 15232 | 240 | 2904 | 6656 | LUTx: 13456 |
| | | 205 | 2326 | 4320 | LUTx: 16288 | | | | | 256 | 1792 | 6656 | LUTx: 7104 |
| 16x16 | 8 | 256 | 0 | 0 | N.A. | 256 | 1024 | 7936 | LUTx: 6096 | 0 | 4096 | 7936 | LUTx: 26368 |
| 16x16 | 16 | 256 | 0 | 0 | N.A. | 256 | 2048 | 15872 | LUTx: 16384 | 256 | 0 | 3088 | N.A. |
| 16x16 | 32 | 768 | 10933 | 36351 | LUTx: 46096 | 1024 | 11520 | 31744 | LUTx: 60928 | 840 | 19956 | 29793 | LUTx: 101464 |
| | | 770 | 9014 | 17296 | LUTx: 64224 | | | | | 1024 | 7168 | 29696 | LUTx: 28416 |

#### MLP
We are assuming a simple PE structure as follows.

```
                rst               
                 │                
            ┌────│────────────┐   
            │    ▼            │   
            │  ┌─┴─┐   ┌───┐  │  c
            └─►┤dff├──►┤ + ├──┴─►─
               │rst│ ┌►┤   │      
               └───┘ │ └───┘      
a    ┌───┐     ┌───┐ │            
────►┤dff├─┬──►┤ * ├─┘            
     │   │ │ ┌►┤   │              
     └───┘ │ │ └───┘             a
b    ┌───┐ └────────────────────►─
────►┤dff├───┴──────────────────►─
     │   │                       b
     └───┘                        
```

And a 2x2 mesh of such PEs is connected as follows (reset ignored for simplicity).

```
        │bi0     │bi1     
    ┌───│────────│────┐   
    │   ▼        ▼    │   
 ai0│ ┌─┴──┐a00┌─┴──┐ │ao0
─────►┤PE00├──►┤PE01├►────
    │ └─┬──┘   └─┬──┘ │   
    │   │b00     │b01 │   
    │   ▼        ▼    │   
 ai1│ ┌─┴──┐a10┌─┴──┐ │ao1
─────►┤PE10├──►┤PE11├►────
    │ └─┬──┘   └─┬──┘ │   
    │   ▼        ▼    │   
    └───│────────│────┘   
        │bo0     │bo1     
```

| Matrix Size | Weight Bitwidth | Target Architecture | Time | Result |
|-------------|-----------------|---------------------|----------|--------|
| 4x4 | 8 | Single MAC PE | 392 ms | Successfully mapped on 16 PEs |
| 4x4 | 8 | 2x2 MAC Mesh | 234 ms | Successfully mapped on 4 Meshes |
| 4x4 | 8 | 4x4 MAC Mesh | 306 ms | Successfully mapped on 1 Mesh |
| 4x4 | 16 | Single MAC PE | 314 ms | Successfully mapped on 16 PEs |
| 4x4 | 16 | 2x2 MAC Mesh | 281 ms | Successfully mapped on 4 Meshes |
| 4x4 | 16 | 4x4 MAC Mesh | 314 ms | Successfully mapped on 1 Mesh |
| 8x8 | 16 | 4x4 MAC Mesh | 2.5 s | Successfully mapped on 4 Meshes |
| 16x16 | 16 | 4x4 MAC Mesh | 42.9 s | Successfully mapped on 16 Meshes |
| Any | 32 | Any | 560 ms | Failed to map |

### FIR Filter
| Taps | Coeff Bitwidth | Nextmap |        |    |                 | Yosys |        |    |                 | Proprietary |        |    |                 |
|------|----------------|---------|--------|----|-----------------|-------|--------|----|-----------------|-------|--------|----|-----------------|
|      |                | DSP     | CARRY4 | FF | Other Resources | DSP   | CARRY4 | FF | Other Resources | DSP   | CARRY4 | FF | Other Resources |
| 16 | 8 | 16 | 44 | 0 | LUTx: 391, MUXFx: 28 | 16 | 4 | 240 | LUTx: 1011, MUXFx: 799 |
| 16 | 16 | 16 | 88 | 0 | LUTx: 791, MUXFx: 60 | 16 | 8 | 496 | LUTx: 2154, MUXFx: 1713 |
| 16 | 32 | 48 | 464 | 0 | LUTx: 8898, MUXFx: 4775 | 64 | 464 | 1008 | LUTx: 6176, MUXFx: 3576 |
| 32 | 8 | 32 | 56 | 0 | LUTx: 1076, MUXFx: 341 | 32 | 4 | 480 | LUTx: 2340, MUXFx: 1909 |
| 32 | 16 | 32 | 112 | 0 | LUTx: 2213, MUXFx: 725 | 32 | 8 | 992 | LUTx: 5140, MUXFx: 4248 |
| 32 | 32 | 96 | 912 | 0 | LUTx: 17999, MUXFx: 9613 | 128 | 912 | 2016 | LUTx: 14024, MUXFx: 8880 |
| 64 | 8 | 64 | 128 | 0 | LUTx: 1577, MUXFx: 7 | 64 | 4 | 960 | LUTx: 5151, MUXFx: 4328 |
| 64 | 16 | 64 | 256 | 0 | LUTx: 3193, MUXFx: 7 | 64 | 8 | 1984 | LUTx: 11088, MUXFx: 9442 | 64 | 0 | 930 | N.A. |
| 64 | 32 | 192 | 1808 | 0 | LUTx: 39246, MUXFx: 23099 | 256 | 1808 | 4032 | LUTx: 29801, MUXFx: 19641 | 256 | 1264 | 1922 | LUTx: 6977 |

### Nerv
In the NERV CPU, all multipliers are constant multipliers. Nextmap leaves them unchanged, and since it does not yet perform advanced logic optimizations, the results are largely the same as the original design. This also demonstrates that Nextmap can handle large designs reliably and preserves the purely logical parts without introducing issues.

| Nextmap |        |    |                 | Yosys |        |    |                 |
|---------|--------|----|-----------------|-------|--------|----|-----------------|
| DSP     | CARRY4 | FF | Other Resources | DSP   | CARRY4 | FF | Other Resources |
| 0 | 895 | 4183 | LUTx: 15132, MUXFx: 6919 | 0 | 904 | 4163 | LUTx: 14028, MUXFx: 7229 |