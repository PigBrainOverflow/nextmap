import os

ABC_PATH = "~/hw/abc/abc"
ASAP7_PATH = "techlib/asap7_clean.lib"


def lutmap(input_eqn_file: str):
    os.system(f"{ABC_PATH} -c 'read {ASAP7_PATH}; read_eqn {input_eqn_file}; st; dch -f; print_stats -p; read_lib {ASAP7_PATH}; map; topo; upsize; dnsize; stime'")

if __name__ == "__main__":
    input_eqn_file = "eval/epfl/bar.eqn"
    lutmap(input_eqn_file)