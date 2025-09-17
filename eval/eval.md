| Name | Description | Wire Count | Cell Count | sqlite     |              | egglog (vanilla) |              | egglog-spec |              |
|------|-------------|------------|------------|------------|--------------|------------------|--------------|----------------|--------------|
|      |             |            |            | Build Time | Rewrite Time | Build Time       | Rewrite Time | Build Time     | Rewrite Time |
| alu_w32 | A simple 32-bit ALU | 1079 | 69 | 0.04 s| 0.03 s | 3.77 s | 0.03 s | 0.04 s | 0.03 s |
| multi_alu_n4_w32 | 4 ALUs of 32 bits each | 4732 | 276 | 0.10 s | 0.03 s | 34.78 s | 0.12 s | 0.15 s | 0.04 s |
| multi_alu_n8_w32 | 8 ALUs of 32 bits each | 9464 | 552 | 0.20 s | 0.03 s | 199.95 s | 0.56 s | 0.24 s | 0.04 s |
| multi_alu_n16_w32 | 16 ALUs of 32 bits each | 18928 | 1104 | 0.51 s | 0.07 s | > 600 s (timeout) | N.A. | 0.63 s | 0.07 s |
| aes_sbox | A 256-bit AES S-box implementation | 11768 | 2548 | 0.73 s | 0.01 s | > 600 s (timeout) | N.A. | 0.82 s | 0.01 s |