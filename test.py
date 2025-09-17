import emap
import json
import time
netlist = emap.Netlist()
with open("eval/out/aes_sbox.json") as f:
    mod = json.load(f)["modules"]["aes_sbox"]

start = time.time()
netlist.build_from_json(mod)
print(f"Build time: {time.time() - start:.2f}s")