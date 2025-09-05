## Evaluation

### Handcrafted
Results by plain cost model:

| Name | Description | Nextmap |        |    |                 | Yosys |        |    |                |
|------|-------------|---------|--------|----|-----------------|-------|--------|----|----------------|
|      |             | DSP     | CARRY4 | FF | Other Resources | DSP   | CARRY4 | FF | Other Resources |
| bad_multiplier | 16-bit truncated multiplier | 1 | 0 | 32 | N.A. | 1 | 0 | 64 | N.A. |
| complex_multiplier | $(a + bi) \times (c + di)$ | 3 | 0 | 64 | N.A. | 4 | 16 | 128 | LUT2: 64 |
| dot_product | $a\times b + c\times d$ | 2 | 0 | 32 | N.A. | 2 | 8 | 64 | LUT2: 32 |
| multiplier_with_rst | 16-bit multiplier with synchronous reset | 1 | 0 | 0 | N.A. | 1 | 0 | 64 | N.A. |
| redundant_adders | Three adders with shared inputs but different widths | 0 | 8 | 0 | LUT: 32 | 0 | 14 | 0 | LUT: 32 |
| signed_mac | $a \times b + c$ | 1 | 0 | 32 | N.A. | 1 | 8 | 64 | LUT2: 32 |
| signed_reg | sign-extension and delay | 0 | 0 | 32 | N.A. | 0 | 0 | 32 | N.A. |
| square_diff | $(a - b)^2$ | 1 | 0 | 64 | N.A. | 1 | 5 | 83 | LUT2: 16 |
| unsigned_mac | $a \times b + c$ | 1 | 0 | 32 | N.A. | 1 | 8 | 64 | LUT2: 32 |
| wide_multiplier | 32-bit multiplier | 2 | 0 | 49 | N.A. | 2 | 4 | 64 | LUT2: 15 |

