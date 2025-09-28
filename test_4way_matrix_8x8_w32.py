#!/usr/bin/env python3
"""
4-way test matrix with resource counting for 8x8_w32: SQLite/PostgreSQL × Gurobi/CBC
Based on eval_systolic.ipynb instead of eval_systolic_v2.ipynb
Includes detailed resource counting from yosys stat outputs
"""

import sys
import os
import time
import json
import re
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath('.'))

import emap

def simple_cost_model(type_: str, *ports) -> float:
    """Standard cost model used in evaluations"""
    if type_ == "$dff":
        return len(ports[0]) * 1.0
    elif type_ in {"$muls", "$mulu"}:
        return len(ports[0]) * len(ports[1]) * 2.0
    elif type_ in {"$adds", "$addu", "$subs", "$subu"}:
        return min(len(ports[0]) + len(ports[1]), len(ports[2])) * 1.0
    return len(ports[0]) * 1.0  # other types

# DSP rules from eval_systolic.ipynb
dsp_rules = {
    "signed_mul_1_stage_27_18_48_bit_with_ab_out": {
        "requirements": {
            "dsp48e2": 1
        },
        "hidden_inputs": ["clk"],
        "inputs": ["a", "b"],
        "outputs": ["a_out", "b_out", "p"],
        "match_sql": """
            SELECT dff_a.d, dff_b.d, mul1.a, mul1.b, mul1.y
            FROM dffs AS dff_a JOIN dffs AS dff_b JOIN aby_cells AS mul1
            ON dff_a.q = mul1.a AND dff_b.q = mul1.b
            WHERE mul1.type = '$muls'
                AND width_of(mul1.a) <= 27 AND width_of(mul1.b) <= 18 AND width_of(mul1.y) <= 48
        """
    },
    "signed_muladd_1_stage_27_18_48_bit_with_ab_out": {
        "requirements": {
            "dsp48e2": 1
        },
        "hidden_inputs": ["clk"],
        "inputs": ["a", "b", "c"],
        "outputs": ["a_out", "b_out", "p"],
        "match_sql": """
            SELECT dff_a.d, dff_b.d, add1.b, mul1.a, mul1.b, mul1.y
            FROM dffs AS dff_a
            JOIN aby_cells AS mul1 ON dff_a.q = mul1.a
            JOIN dffs AS dff_b ON dff_b.q = mul1.b
            JOIN aby_cells AS add1 ON mul1.y = add1.a
            WHERE mul1.type = '$muls' AND add1.type = '$adds'
                AND width_of(mul1.a) <= 27 AND width_of(mul1.b) <= 18 AND width_of(add1.b) <= 48 AND width_of(mul1.y) <= 48
        """
    },
    "signed_addmulsub_1_stage_26_18_48_26_bit": {
        "requirements": {
            "dsp48e2": 1
        },
        "hidden_inputs": ["clk"],
        "inputs": ["a", "d", "b", "c"],
        "outputs": ["p"],
        "match_sql": """
            SELECT add2.a, add2.b, mul1.b, sub1.b, dff1.q
            FROM dffs AS dff1
            JOIN aby_cells AS sub1 ON dff1.d = sub1.y
            JOIN aby_cells AS mul1 ON mul1.y = sub1.a
            JOIN aby_cells AS add2 ON add2.y = mul1.a
            WHERE add2.type = '$adds' AND mul1.type = '$muls' AND sub1.type = '$subs'
                AND width_of(add2.a) <= 26 AND width_of(add2.b) <= 26 AND width_of(mul1.b) <= 18 AND width_of(sub1.b) <= 48 AND width_of(dff1.q) <= 48
        """
    },
}

def check_postgresql_available() -> bool:
    """Check if PostgreSQL is available"""
    try:
        import psycopg2
        import getpass
        conn = psycopg2.connect(database='postgres', user=getpass.getuser())
        conn.close()
        return True
    except Exception:
        return False

def check_gurobi_available() -> bool:
    """Check if Gurobi is available"""
    try:
        from emap.extracts.solver_interface import create_solver
        solver = create_solver("gurobi")
        return True
    except Exception:
        return False

def check_cbc_available() -> bool:
    """Check if CBC is available"""
    try:
        from emap.extracts.solver_interface import create_solver
        solver = create_solver("cbc")
        return True
    except Exception:
        return False

def cleanup_postgresql_database() -> bool:
    """Clean up PostgreSQL database before running tests"""
    try:
        import psycopg2
        import getpass

        # Connect and drop/recreate the database
        conn = psycopg2.connect(database='postgres', user=getpass.getuser())
        conn.autocommit = True
        cur = conn.cursor()

        # Terminate any active connections to the target database
        cur.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'nextmap_temp' AND pid <> pg_backend_pid()
        """)

        # Drop and recreate the database
        cur.execute("DROP DATABASE IF EXISTS nextmap_temp")
        cur.execute("CREATE DATABASE nextmap_temp")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"PostgreSQL database cleanup failed: {e}")
        return False

def parse_yosys_stat(stat_file_path: str) -> dict:
    """Parse yosys stat output to extract resource counts"""
    resources = {}
    try:
        with open(stat_file_path, 'r') as f:
            content = f.read()

        # Extract resource counts using regex patterns for actual yosys output
        patterns = {
            'lut2': r'(\d+)\s+LUT2',
            'lut3': r'(\d+)\s+LUT3',
            'lut4': r'(\d+)\s+LUT4',
            'lut5': r'(\d+)\s+LUT5',
            'lut6': r'(\d+)\s+LUT6',
            'ffs': r'(\d+)\s+FDRE',
            'carry4': r'(\d+)\s+CARRY4',
            'carry8': r'(\d+)\s+CARRY8',
            'bufg': r'(\d+)\s+BUFG',
            'bram': r'(\d+)\s+RAMB\w+',
            'dsp_mul': r'(\d+)\s+signed_mul_1_stage_27_18_48_bit_with_ab_out',
            'dsp_muladd': r'(\d+)\s+signed_muladd_1_stage_27_18_48_bit_with_ab_out',
            'dsp_addmulsub': r'(\d+)\s+signed_addmulsub_1_stage_26_18_48_26_bit',
        }

        for resource, pattern in patterns.items():
            match = re.search(pattern, content)
            resources[resource] = int(match.group(1)) if match else 0

        # Calculate total LUTs and total DSPs
        resources['luts'] = sum(resources.get(f'lut{i}', 0) for i in range(2, 7))
        resources['dsps'] = resources.get('dsp_mul', 0) + resources.get('dsp_muladd', 0) + resources.get('dsp_addmulsub', 0)
        resources['carry'] = resources.get('carry4', 0) + resources.get('carry8', 0)
        resources['brams'] = resources.get('bram', 0)

    except Exception as e:
        print(f"Warning: Could not parse stat file {stat_file_path}: {e}")
        resources = {'luts': 0, 'ffs': 0, 'dsps': 0, 'brams': 0, 'carry': 0, 'bufg': 0}

    return resources

def run_yosys_synthesis(test_name: str) -> dict:
    """Run yosys synthesis and extract resource counts"""
    original_stat_file = f"eval/out/{test_name}.stat"
    extracted_stat_file = f"eval/out/{test_name}_extracted.stat"

    # Ensure output directory exists
    os.makedirs("eval/out", exist_ok=True)

    original_resources = {}
    extracted_resources = {}

    try:
        # Generate original design stats if they don't exist
        if not os.path.exists(original_stat_file):
            verilog_file = f"eval/systolic/{test_name}.v"
            if os.path.exists(verilog_file):
                cmd = f'yosys -q -p "read_verilog {verilog_file}; proc; memory_map; opt; synth_xilinx -family xcup; tee -o {original_stat_file} stat" 2>/dev/null'
                os.system(cmd)

        # Parse original resources
        if os.path.exists(original_stat_file):
            original_resources = parse_yosys_stat(original_stat_file)

        # Parse extracted resources
        if os.path.exists(extracted_stat_file):
            extracted_resources = parse_yosys_stat(extracted_stat_file)

    except Exception as e:
        print(f"Warning: Yosys synthesis failed for {test_name}: {e}")

    return {
        'original': original_resources,
        'extracted': extracted_resources
    }

def patch_postgres_queries():
    """Patch emap's PostgreSQL query execution to handle reserved column names"""
    import emap.db_postgres
    import emap.db_interface

    # Save original execute methods for all possible paths
    original_adapter_execute = emap.db_postgres.PostgreSQLAdapter.execute
    original_netlistdb_execute = emap.db_postgres.NetlistDB.execute
    original_interface_execute = emap.db_interface.NetlistDB.execute

    def patched_adapter_execute(self, query: str, params=None):
        """Patched adapter execute that translates queries for PostgreSQL"""
        query = translate_query_to_postgres(query)
        return original_adapter_execute(self, query, params)

    def patched_netlistdb_execute(self, query: str, params=None):
        """Patched NetlistDB execute that translates queries for PostgreSQL"""
        query = translate_query_to_postgres(query)
        return original_netlistdb_execute(self, query, params)

    def patched_interface_execute(self, query: str, params=None):
        """Patched interface execute that translates queries for PostgreSQL"""
        # Check if this is PostgreSQL backend
        if hasattr(self._adapter, 'connection') and self._adapter.connection:
            query = translate_query_to_postgres(query)
        return original_interface_execute(self, query, params)

    # Replace all execute methods
    emap.db_postgres.PostgreSQLAdapter.execute = patched_adapter_execute
    emap.db_postgres.NetlistDB.execute = patched_netlistdb_execute
    emap.db_interface.NetlistDB.execute = patched_interface_execute

def translate_query_to_postgres(query: str) -> str:
    """Translate SQLite queries to PostgreSQL compatible format"""
    # First convert SQLite parameter placeholders to PostgreSQL format
    query = query.replace('?', '%s')

    # Quote reserved column names in PostgreSQL
    reserved_words = ['a', 'b', 'y', 'type']

    for word in reserved_words:
        # Quote column names in various contexts
        query = re.sub(f'\\b{word}\\s*=', f'"{word}" =', query)
        query = re.sub(f'SELECT\\s+{word}\\b', f'SELECT "{word}"', query)
        query = re.sub(f'SELECT\\s+([^,]*,\\s*)*{word}\\b', lambda m: m.group(0).replace(word, f'"{word}"'), query)
        query = re.sub(f'\\.{word}\\b', f'."{word}"', query)
        query = re.sub(f'\\b{word}\\s*,', f'"{word}",', query)
        query = re.sub(f',\\s*{word}\\b', f', "{word}"', query)

    return query

def run_systolic_test(test_name: str, dsp_limit: int, database_backend: str, solver_backend: str) -> dict:
    """Run systolic test with specified database and solver backends"""
    config_name = f"{database_backend}+{solver_backend}"
    print(f"  {config_name}: Running {test_name}...")

    db_file = None
    try:
        start_time = time.time()

        # Phase 1: Database initialization
        init_start = time.time()
        if database_backend == "sqlite":
            # Use temporary SQLite file
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
                db_file = tmp_db.name
            netlist = emap.NetlistDB("emap/schema.sql", db_file, backend='sqlite')
        else:  # postgresql
            # Clean PostgreSQL database first
            if not cleanup_postgresql_database():
                return {
                    'test': test_name, 'database': database_backend, 'solver': solver_backend,
                    'success': False, 'error': 'Database cleanup failed'
                }
            # Use the factory function without specifying schema - it will auto-select PostgreSQL schema
            netlist = emap.NetlistDB("emap/schema.sql", None, backend='postgres')

            # The PostgreSQL adapter now handles translation automatically,
            # so no additional patching is needed

        # Load and build JSON
        with open(f'eval/out/{test_name}.json', 'r') as f:
            json_data = json.load(f)
        netlist.build_from_json(json_data['modules']['top'])
        netlist.rebuild()
        init_time = time.time() - init_start

        # Phase 2: Apply wide splits (specific to w32 designs from eval_systolic.ipynb)
        wide_split_start = time.time()
        wide_split_rewrites = 0

        # Wide multiplier splits
        matches = emap.rewrites.ematch_wide_muls(netlist)
        cnt = emap.rewrites.apply_wide_muls_split(netlist, matches)
        wide_split_rewrites += cnt
        if cnt > 0:
            netlist.rebuild()

        # Wide DFF splits
        matches = emap.rewrites.ematch_wide_dff(netlist)
        cnt = emap.rewrites.apply_wide_dff_split(netlist, matches)
        wide_split_rewrites += cnt
        if cnt > 0:
            netlist.rebuild()

        wide_split_time = time.time() - wide_split_start

        # Phase 3: Apply rewrites (based on eval_systolic.ipynb)
        rewrite_start = time.time()
        total_rewrites = 0
        iterations = 0
        cnt = 1

        while cnt > 0:
            iterations += 1
            cnt = 0

            # Apply rewrites
            comm_matches = emap.rewrites.ematch_comm(netlist, ["$adds", "$muls"])
            cnt += emap.rewrites.apply_comm(netlist, comm_matches)

            dff_forward_aby_cell_matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ["$adds", "$muls"])
            cnt += emap.rewrites.apply_dff_forward_aby_cell(netlist, dff_forward_aby_cell_matches)

            dff_backward_aby_cell_matches = emap.rewrites.ematch_dff_backward_aby_cell(netlist, ["$adds", "$muls"])
            cnt += emap.rewrites.apply_dff_backward_aby_cell(netlist, dff_backward_aby_cell_matches)

            total_rewrites += cnt
            if cnt > 0:
                netlist.rebuild()

        # Apply SDFF rewrites (from eval_systolic.ipynb)
        sdff_start = time.time()
        sdff_rewrites = emap.rewrites.rewrite_sdff(netlist)
        sdff_time = time.time() - sdff_start

        rewrite_time = time.time() - rewrite_start

        # Phase 4: Tech mapping (using eval_systolic.ipynb approach)
        techmap_start = time.time()
        emap.rewrites.create_tech_tables(netlist, dsp_rules)
        emap.rewrites.rewrite_tech(netlist, dsp_rules)  # Different from eval_systolic_v2.ipynb
        techmap_time = time.time() - techmap_start

        # Phase 5: ILP extraction with specified solver
        extraction_start = time.time()
        mod = emap.extracts.ilp.extract_techmap_with_limit(
            netlist,
            simple_cost_model,
            dsp_rules,
            {"dsp48e2": dsp_limit},
            solver_type=solver_backend.lower(),
            OutputFlag=False
        )
        extraction_time = time.time() - extraction_start

        # Phase 6: Generate extracted JSON and run yosys synthesis for resource counting
        synthesis_start = time.time()
        extracted_json_path = f"eval/out/{test_name}_extracted.json"
        with open(extracted_json_path, "w") as f:
            json.dump({"creator": "nextmap", "modules": {"top": mod}}, f, indent=2)

        # Run yosys synthesis on extracted design for resource counting
        extracted_stat_file = f"eval/out/{test_name}_extracted.stat"
        yosys_cmd = f'yosys -q -p "read_json {extracted_json_path}; read_verilog eval/blackboxes/dsp_defs.v; synth_xilinx -family xcup; tee -o {extracted_stat_file} stat" 2>/dev/null'
        os.system(yosys_cmd)

        synthesis_time = time.time() - synthesis_start

        # Phase 7: Parse resource counts
        resource_data = run_yosys_synthesis(test_name)

        # Results
        total_time = time.time() - start_time
        num_cells = len(mod.get('cells', {}))
        dsp_cells = sum(1 for cell in mod.get('cells', {}).values()
                       if any(rule_name in cell.get('type', '') for rule_name in dsp_rules.keys()))

        # Cleanup SQLite file
        if db_file and os.path.exists(db_file):
            try:
                os.unlink(db_file)
            except:
                pass

        return {
            'test': test_name,
            'database': database_backend,
            'solver': solver_backend,
            'config': config_name,
            'success': True,
            'total_time': total_time,
            'init_time': init_time,
            'rewrite_time': rewrite_time,
            'wide_split_time': wide_split_time,
            'sdff_time': sdff_time,
            'techmap_time': techmap_time,
            'extraction_time': extraction_time,
            'synthesis_time': synthesis_time,
            'total_rewrites': total_rewrites,
            'wide_split_rewrites': wide_split_rewrites,
            'sdff_rewrites': sdff_rewrites,
            'iterations': iterations,
            'cells': num_cells,
            'dsps': dsp_cells,
            'dsp_limit': dsp_limit,
            'resources': resource_data
        }

    except Exception as e:
        # Cleanup on error
        if db_file and os.path.exists(db_file):
            try:
                os.unlink(db_file)
            except:
                pass

        return {
            'test': test_name,
            'database': database_backend,
            'solver': solver_backend,
            'config': config_name,
            'success': False,
            'error': str(e)
        }

def run_4way_test():
    """Run the 8x8_w32 test across all 4 backend+solver combinations."""

    # PostgreSQL compatibility is now handled automatically in the database layer
    # patch_postgres_queries()

    # Test configuration for 8x8_w32 (from eval_systolic.ipynb)
    test_name = "systolic_matmul_8x8_w32"
    dsp_limit = 192  # From eval_systolic.ipynb

    # Check available backends and solvers
    print("Checking availability...")
    postgres_available = check_postgresql_available()
    gurobi_available = check_gurobi_available()
    cbc_available = check_cbc_available()

    print(f"  PostgreSQL: {'✅' if postgres_available else '❌'}")
    print(f"  Gurobi: {'✅' if gurobi_available else '❌'}")
    print(f"  CBC: {'✅' if cbc_available else '❌'}")
    print()

    # Define test matrix
    database_backends = ['sqlite']
    solver_backends = []

    if postgres_available:
        database_backends.append('postgresql')

    if gurobi_available:
        solver_backends.append('gurobi')

    if cbc_available:
        solver_backends.append('cbc')

    if not solver_backends:
        print("❌ No solvers available! Cannot run tests.")
        return

    # Ensure required files exist
    json_path = f'eval/out/{test_name}.json'
    if not os.path.exists(json_path):
        verilog_path = f'eval/systolic/{test_name}.v'
        if os.path.exists(verilog_path):
            print(f"Generating {json_path} from {verilog_path}...")
            os.makedirs("eval/out", exist_ok=True)
            cmd = f'yosys -q -p "read_verilog {verilog_path}; proc; memory_map; opt; write_json {json_path}" 2>/dev/null'
            os.system(cmd)
        else:
            print(f"❌ Neither {json_path} nor {verilog_path} found!")
            return

    # Run test matrix
    results = []
    total_configs = len(database_backends) * len(solver_backends)

    print(f"Running {total_configs} test configurations for {test_name}:")
    print("="*80)

    for db_backend in database_backends:
        for solver_backend in solver_backends:
            config_name = f"{db_backend}+{solver_backend}"
            print(f"Testing {config_name}...")

            try:
                result = run_systolic_test(test_name, dsp_limit, db_backend, solver_backend)
                results.append(result)

                if result['success']:
                    # Print timing and resource info
                    resources = result.get('resources', {})
                    extracted = resources.get('extracted', {})
                    print(f"  ✅ SUCCESS")
                    print(f"     Time: {result['total_time']:.2f}s")
                    print(f"     Rewrites: {result['total_rewrites']} (wide_splits: {result['wide_split_rewrites']})")
                    print(f"     DSPs: {result['dsps']}")
                    print(f"     Resources: LUTs={extracted.get('luts', 0)}, FFs={extracted.get('ffs', 0)}, DSPs={extracted.get('dsps', 0)}, BRAMs={extracted.get('brams', 0)}")
                else:
                    print(f"  ❌ FAILED - {result.get('error', 'Unknown error')}")

            except Exception as e:
                print(f"  ❌ EXCEPTION - {e}")
                results.append({
                    'test': test_name,
                    'database': db_backend,
                    'solver': solver_backend,
                    'config': config_name,
                    'success': False,
                    'error': str(e)
                })

            print()

    # Summary
    print("="*80)
    print("TEST SUMMARY:")
    print("="*80)

    successful_configs = [r for r in results if r['success']]
    failed_configs = [r for r in results if not r['success']]

    print(f"✅ Successful: {len(successful_configs)}/{len(results)} configurations")
    print(f"❌ Failed: {len(failed_configs)}/{len(results)} configurations")
    print()

    if successful_configs:
        print("SUCCESSFUL CONFIGURATIONS:")
        print(f"{'Config':<18} {'Time(s)':<8} {'Rewrites':<9} {'WSplits':<8} {'DSPs':<5} {'LUTs':<6} {'FFs':<6} {'BRAMs':<6}")
        print("-" * 80)
        for result in successful_configs:
            resources = result.get('resources', {}).get('extracted', {})
            print(f"{result['config']:<18} {result['total_time']:<8.2f} {result['total_rewrites']:<9} {result['wide_split_rewrites']:<8} {result['dsps']:<5} {resources.get('luts', 0):<6} {resources.get('ffs', 0):<6} {resources.get('brams', 0):<6}")
        print()

    if failed_configs:
        print("FAILED CONFIGURATIONS:")
        for result in failed_configs:
            error_summary = result.get('error', 'Unknown error')
            if len(error_summary) > 100:
                error_summary = error_summary[:100] + "..."
            print(f"  {result['config']}: {error_summary}")
        print()

    # Performance comparison for successful configs
    if len(successful_configs) > 1:
        print("PERFORMANCE COMPARISON:")
        successful_configs.sort(key=lambda x: x['total_time'])
        fastest = successful_configs[0]
        print(f"  Fastest: {fastest['config']} ({fastest['total_time']:.2f}s)")

        for result in successful_configs[1:]:
            slowdown = result['total_time'] / fastest['total_time']
            print(f"  {result['config']}: {result['total_time']:.2f}s ({slowdown:.2f}x slower)")

    # Save detailed results
    with open('4way_test_results_8x8_w32.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: 4way_test_results_8x8_w32.json")

    return len(successful_configs) == len(results)

if __name__ == "__main__":
    success = run_4way_test()
    if success:
        print("\n🎉 ALL CONFIGURATIONS PASSED!")
        sys.exit(0)
    else:
        print("\n💥 SOME CONFIGURATIONS FAILED!")
        sys.exit(1)
