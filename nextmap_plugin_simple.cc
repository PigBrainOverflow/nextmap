#include "kernel/yosys.h"
#include "kernel/sigtools.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <cstdlib>

YOSYS_NAMESPACE_BEGIN

struct NextmapPass : public Pass {
    NextmapPass() : Pass("nextmap", "Apply nextmap optimization passes") { }

    void help() override
    {
        log("\n");
        log("    nextmap [options] [selection]\n");
        log("\n");
        log("Apply nextmap optimization and rewrite passes to the current design.\n");
        log("\n");
        log("    -temp_dir <path>\n");
        log("        specify temporary directory for intermediate files\n");
        log("        (default: /tmp)\n");
        log("\n");
        log("    -schema <path>\n");
        log("        specify path to nextmap schema file\n");
        log("        (default: ./emap/schema.sql)\n");
        log("\n");
        log("    -iterations <n>\n");
        log("        maximum number of rewrite iterations\n");
        log("        (default: 10)\n");
        log("\n");
        log("    -runner <path>\n");
        log("        path to nextmap_runner.py script\n");
        log("        (default: ./nextmap_runner.py)\n");
        log("\n");
        log("    -strategy <type>\n");
        log("        optimization strategy: basic, retiming, comprehensive, dsp\n");
        log("        (default: basic)\n");
        log("\n");
    }

    void execute(std::vector<std::string> args, RTLIL::Design *design) override
    {
        std::string temp_dir = "/tmp";
        std::string schema_path = "./emap/schema.sql";
        std::string runner_path = "./nextmap_runner.py";
        std::string strategy = "basic";
        int max_iterations = 10;

        size_t argidx;
        for (argidx = 1; argidx < args.size(); argidx++)
        {
            if (args[argidx] == "-temp_dir" && argidx+1 < args.size()) {
                temp_dir = args[++argidx];
                continue;
            }
            if (args[argidx] == "-schema" && argidx+1 < args.size()) {
                schema_path = args[++argidx];
                continue;
            }
            if (args[argidx] == "-iterations" && argidx+1 < args.size()) {
                max_iterations = std::stoi(args[++argidx]);
                continue;
            }
            if (args[argidx] == "-runner" && argidx+1 < args.size()) {
                runner_path = args[++argidx];
                continue;
            }
            if (args[argidx] == "-strategy" && argidx+1 < args.size()) {
                strategy = args[++argidx];
                continue;
            }
            break;
        }
        extra_args(args, argidx, design);

        log_header(design, "Executing NEXTMAP pass.\n");

        // Generate temporary filenames
        std::string input_json = temp_dir + "/nextmap_input.json";
        std::string output_json = temp_dir + "/nextmap_output.json";

        try {
            // Export current design to JSON
            log("Exporting design to JSON...\n");
            run_pass("write_json " + input_json, design);

            // Check if input file was created
            std::ifstream check_input(input_json);
            if (!check_input.good()) {
                log_error("Failed to export design to JSON\n");
                return;
            }
            check_input.close();

            // Prepare command to run nextmap_runner.py
            std::string command = "python3 " + runner_path +
                                " \"" + input_json + "\"" +
                                " \"" + output_json + "\"" +
                                " --schema \"" + schema_path + "\"" +
                                " --iterations " + std::to_string(max_iterations) +
                                " --strategy " + strategy;

            log("Running nextmap optimization...\n");
            log("Command: %s\n", command.c_str());

            // Execute the Python script
            int result = std::system(command.c_str());

            if (result != 0) {
                log_error("Nextmap runner failed with exit code %d\n", result);
                return;
            }

            // Check if output file was created
            std::ifstream check_output(output_json);
            if (!check_output.good()) {
                log_error("Nextmap optimization failed - no output file generated\n");
                return;
            }
            check_output.close();

            // Load optimized version - this will replace the current modules
            log("Loading optimized design...\n");
            run_pass("design -reset", design);  // Clear design first
            run_pass("read_json " + output_json, design);

            // Clean up temporary files
            std::remove(input_json.c_str());
            std::remove(output_json.c_str());

            log("Nextmap optimization completed successfully.\n");

        } catch (const std::exception& e) {
            log_error("Exception during nextmap execution: %s\n", e.what());
        }
    }
} NextmapPass;

YOSYS_NAMESPACE_END