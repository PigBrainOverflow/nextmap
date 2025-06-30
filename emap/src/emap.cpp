#include "kernel/yosys.h"
#include <kernel/yosys_common.h>
#include <kernel/functional.h>

#ifndef UNUSED
#define UNUSED(x) (void)(x)
#endif


USING_YOSYS_NAMESPACE
PRIVATE_NAMESPACE_BEGIN

struct MyPass : public Pass {
    MyPass() : Pass("my_cmd", "just a simple test") { }
    void execute(std::vector<std::string> args, RTLIL::Design *design) override
    {
        UNUSED(args);
        for (auto mod : design->modules()) {
            auto fmod = Functional::IR::from_module(mod);
            fmod.
        }
    }
} MyPass;

// struct FunctionalIRDumpPass : public Pass {
//     FunctionalIRDumpPass() 

// struct DumpPass : public Pass {
//     DumpPass() : Pass("oda_dump", "dump the design by Odaviv") {}

//     void log_help() const {
//         log("\n");
//         log("    dump [<filename>]\n");
//         log("\n");
//         log("Dump the current design in JSON format.\n");
//         log("If <filename> is not specified, the output is printed to stdout.\n");
//         log("\n");
//     }

//     void execute(std::vector<std::string> args, RTLIL::Design* design) override {
//         if (args.size() == 1) { // output to stdout
//             auto design_json = Odaviv::to_json(design);
//             log("RTLIL in JSON:\n%s\n", design_json.dump().c_str());
//         }
//         else if (args.size() == 2) { // output to file
//             const auto& filename = args[1];
//             auto design_json = Odaviv::to_json(design);
//             std::ofstream file(args[1]);
//             if (file.is_open()) {
//                 file << design_json.dump();
//                 file.close();
//                 log("Design dumped to %s\n", filename.c_str());
//             }
//             else {
//                 log_error("Could not open file %s for writing.\n", filename.c_str());
//             }
//         }
//         else {  // invalid number of arguments
//             log_error("Invalid number of arguments.\n");
//             log_help();
//         }
//     }
// } dump_pass;


PRIVATE_NAMESPACE_END