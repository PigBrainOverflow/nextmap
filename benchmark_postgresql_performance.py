#!/usr/bin/env python3
"""
PostgreSQL Performance Benchmark for Nextmap
Measures detailed runtime performance to compare against SQLite baseline
"""

import sys
import os
import json
import time
import subprocess
from pathlib import Path
import statistics

# Add the project root to the path
sys.path.insert(0, '/home/jbalkind/projects/nextmap')

# Activate venv for CBC support
venv_path = '/home/jbalkind/projects/nextmap/venv/lib/python3.12/site-packages'
if venv_path not in sys.path and os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

import emap

def cleanup_database():
    """Clean up the database before running tests"""
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

    except Exception as e:
        print(f"Warning: Could not clean up database: {e}")

def simple_cost_model(type_: str, *ports) -> float:
    """Standard cost model used in evaluations"""
    if type_ == "$dff":
        return len(ports[0]) * 1.0
    elif type_ in {"$muls", "$mulu"}:
        return len(ports[0]) * len(ports[1]) * 1.0
    elif type_ in {"$adds", "$addu", "$subs", "$subu"}:
        return min(len(ports[0]) + len(ports[1]), len(ports[2])) * 1.0
    return len(ports[0]) * 1.0

# DSP rules from the evaluation notebooks
dsp_rules = {
    "signed_mul_1_stage_26_17_48_bit": {
        "requirements": {"dsp48e2": 1},
        "hidden_inputs": ["clk"],
        "inputs": ["a", "b"],
        "outputs": ["p"],
        "match_sql": """
            SELECT mul1.a, mul1.b, dff1.q
            FROM dffs AS dff1 JOIN aby_cells AS mul1
            ON dff1.d = mul1.y
            WHERE mul1.type = '$muls'
                AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = mul1.a) <= 26
                AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = mul1.b) <= 17
                AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = dff1.q) <= 48
        """
    },
    "signed_muladd_1_stage_26_17_48_bit": {
        "requirements": {"dsp48e2": 1},
        "hidden_inputs": ["clk"],
        "inputs": ["a", "b", "c"],
        "outputs": ["p"],
        "match_sql": """
            SELECT mul1.a, mul1.b, add1.b, dff1.q
            FROM dffs AS dff1
            JOIN aby_cells AS add1 ON dff1.d = add1.y
            JOIN aby_cells AS mul1 ON mul1.y = add1.a
            WHERE mul1.type = '$muls' AND add1.type = '$adds'
                AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = mul1.a) <= 26
                AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = mul1.b) <= 17
                AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = add1.b) <= 48
                AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = dff1.q) <= 48
        """
    },
    "unsigned_muladd_1_stage_27_18_48_bit": {
        "requirements": {"dsp48e2": 1},
        "hidden_inputs": ["clk"],
        "inputs": ["a", "b", "c"],
        "outputs": ["p"],
        "match_sql": """
            SELECT mul1.a, mul1.b, add1.b, dff1.q
            FROM dffs AS dff1
            JOIN aby_cells AS add1 ON dff1.d = add1.y
            JOIN aby_cells AS mul1 ON mul1.y = add1.a
            WHERE mul1.type = '$mulu' AND add1.type = '$addu'
                AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = mul1.a) <= 27
                AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = mul1.b) <= 18
                AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = add1.b) <= 48
                AND (SELECT MAX(idx) + 1 FROM wirevec_members WHERE wirevec = dff1.q) <= 48
        """
    }
}

class TimingProfiler:
    """Detailed timing profiler for database operations"""

    def __init__(self):
        self.timings = {}
        self.start_times = {}

    def start(self, operation):
        self.start_times[operation] = time.time()

    def end(self, operation):
        if operation in self.start_times:
            elapsed = time.time() - self.start_times[operation]
            if operation not in self.timings:
                self.timings[operation] = []
            self.timings[operation].append(elapsed)
            del self.start_times[operation]
            return elapsed
        return 0

    def get_summary(self):
        summary = {}
        for operation, times in self.timings.items():
            summary[operation] = {
                'total': sum(times),
                'average': statistics.mean(times),
                'count': len(times),
                'min': min(times),
                'max': max(times)
            }
        return summary

def benchmark_extraction_flow(test_name, json_path, dsp_limit, runs=3):
    """Benchmark complete extraction flow with detailed timing"""

    print(f"\n=== Benchmarking {test_name} (PostgreSQL) ===")
    print(f"Running {runs} iterations for statistical accuracy")

    all_results = []

    for run in range(runs):
        print(f"\nRun {run + 1}/{runs}:")

        # Clean up database before each run
        cleanup_database()

        profiler = TimingProfiler()
        result = {}

        try:
            # Step 1: Database initialization and JSON loading
            profiler.start('db_init')
            netlist = emap.NetlistDB("emap/schema.sql")
            profiler.end('db_init')

            profiler.start('json_load')
            with open(json_path, "r") as f:
                json_data = json.load(f)
            profiler.end('json_load')

            profiler.start('build_from_json')
            netlist.build_from_json(json_data["modules"]["top"])
            profiler.end('build_from_json')

            profiler.start('initial_rebuild')
            netlist.rebuild()
            profiler.end('initial_rebuild')

            # Step 2: Equality saturation rewrites
            profiler.start('rewrites_total')
            cnt = 1
            total_rewrites = 0
            rewrite_iterations = 0

            while cnt > 0:
                rewrite_iterations += 1
                profiler.start('ematch_operations')
                comm_matches = emap.rewrites.ematch_comm(netlist, ["$adds", "$muls"])
                dff_forward_matches = emap.rewrites.ematch_dff_forward_aby_cell(netlist, ["$adds", "$muls"])
                dff_backward_matches = emap.rewrites.ematch_dff_backward_aby_cell(netlist, ["$adds", "$muls"])
                profiler.end('ematch_operations')

                profiler.start('apply_rewrites')
                cnt = emap.rewrites.apply_comm(netlist, comm_matches)
                cnt += emap.rewrites.apply_dff_forward_aby_cell(netlist, dff_forward_matches)
                cnt += emap.rewrites.apply_dff_backward_aby_cell(netlist, dff_backward_matches)
                total_rewrites += cnt
                profiler.end('apply_rewrites')

                if cnt > 0:
                    profiler.start('rebuild_after_rewrites')
                    netlist.rebuild()
                    profiler.end('rebuild_after_rewrites')

            profiler.end('rewrites_total')

            # Step 3: Technology mapping
            profiler.start('tech_mapping')
            emap.rewrites.create_tech_tables(netlist, dsp_rules)
            emap.rewrites.rewrite_tech(netlist, dsp_rules)
            profiler.end('tech_mapping')

            # Step 4: ILP extraction with CBC
            profiler.start('ilp_extraction')
            mod = emap.extracts.ilp.extract_techmap_with_limit(
                netlist,
                simple_cost_model,
                dsp_rules,
                {"dsp48e2": dsp_limit},
                solver_type="cbc"
            )
            profiler.end('ilp_extraction')

            # Collect results
            result = {
                'run': run + 1,
                'test_name': test_name,
                'total_rewrites': total_rewrites,
                'rewrite_iterations': rewrite_iterations,
                'netlist_cells': len(mod.get('cells', {})),
                'timings': profiler.get_summary()
            }

            # Calculate total time
            timing_summary = profiler.get_summary()
            total_time = sum(t['total'] for t in timing_summary.values())
            result['total_time'] = total_time

            print(f"  Total time: {total_time:.3f}s")
            print(f"  Rewrites: {total_rewrites} in {rewrite_iterations} iterations")
            print(f"  Output cells: {len(mod.get('cells', {}))}")

            all_results.append(result)

        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()
            continue

    return all_results

def analyze_performance_results(all_results):
    """Analyze and summarize performance results"""

    if not all_results:
        print("No successful results to analyze")
        return

    print(f"\n{'='*80}")
    print("POSTGRESQL PERFORMANCE ANALYSIS")
    print(f"{'='*80}")

    # Group results by test name
    by_test = {}
    for result in all_results:
        test_name = result['test_name']
        if test_name not in by_test:
            by_test[test_name] = []
        by_test[test_name].append(result)

    for test_name, results in by_test.items():
        print(f"\n{test_name}:")
        print("-" * 50)

        # Overall timing statistics
        total_times = [r['total_time'] for r in results]
        print(f"Total Runtime:")
        print(f"  Average: {statistics.mean(total_times):.3f}s")
        print(f"  Min: {min(total_times):.3f}s")
        print(f"  Max: {max(total_times):.3f}s")
        if len(total_times) > 1:
            print(f"  StdDev: {statistics.stdev(total_times):.3f}s")

        # Detailed operation breakdown (using first run as representative)
        first_result = results[0]
        timings = first_result['timings']

        print(f"\nDetailed Breakdown:")
        operation_order = [
            'db_init', 'json_load', 'build_from_json', 'initial_rebuild',
            'rewrites_total', 'tech_mapping', 'ilp_extraction'
        ]

        for op in operation_order:
            if op in timings:
                t = timings[op]
                print(f"  {op:<20}: {t['total']:.3f}s ({t['total']/sum(tt['total'] for tt in timings.values())*100:.1f}%)")

        # Rewrite statistics
        rewrites = [r['total_rewrites'] for r in results]
        iterations = [r['rewrite_iterations'] for r in results]
        print(f"\nRewrite Statistics:")
        print(f"  Avg Rewrites: {statistics.mean(rewrites):.0f}")
        print(f"  Avg Iterations: {statistics.mean(iterations):.0f}")

def main():
    """Run PostgreSQL performance benchmarks"""

    print("=== POSTGRESQL PERFORMANCE BENCHMARK ===")
    print("Measuring detailed runtime performance for comparison with SQLite")

    os.chdir('/home/jbalkind/projects/nextmap')

    # Ensure output directory exists
    os.makedirs("eval/out", exist_ok=True)

    # Test cases (same as eval notebooks)
    test_cases = [
        {
            'name': 'fir_n16_w8',
            'verilog': 'eval/fir/fir_n16_w8.v',
            'json': 'eval/out/fir_n16_w8.json',
            'dsp_limit': 16
        },
        {
            'name': 'fir_n16_w16',
            'verilog': 'eval/fir/fir_n16_w16.v',
            'json': 'eval/out/fir_n16_w16.json',
            'dsp_limit': 16
        },
        {
            'name': 'fir_n16_w32',
            'verilog': 'eval/fir/fir_n16_w32.v',
            'json': 'eval/out/fir_n16_w32.json',
            'dsp_limit': 6
        },
        {
            'name': 'fir_n32_w8',
            'verilog': 'eval/fir/fir_n32_w8.v',
            'json': 'eval/out/fir_n32_w8.json',
            'dsp_limit': 32
        }
    ]

    # Generate JSON files if needed
    for test_case in test_cases:
        if os.path.exists(test_case['verilog']) and not os.path.exists(test_case['json']):
            print(f"Generating {test_case['json']}...")
            cmd = f'yosys -q -p "read_verilog {test_case["verilog"]}; proc; opt_merge; opt_clean; write_json {test_case["json"]}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Warning: Could not generate {test_case['json']}")

    # Run benchmarks
    all_results = []
    for test_case in test_cases:
        if os.path.exists(test_case['json']):
            results = benchmark_extraction_flow(
                test_case['name'],
                test_case['json'],
                test_case['dsp_limit'],
                runs=3  # Multiple runs for statistical accuracy
            )
            all_results.extend(results)
        else:
            print(f"Skipping {test_case['name']}: {test_case['json']} not found")

    # Analyze results
    analyze_performance_results(all_results)

    # Save detailed results to JSON for further analysis
    output_file = "postgresql_performance_results.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\nDetailed results saved to {output_file}")
    print("\n🕒 PostgreSQL performance benchmark completed!")
    print("   Use this data to compare against your SQLite baseline measurements")

if __name__ == "__main__":
    main()