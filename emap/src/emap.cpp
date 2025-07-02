#include <iostream>
#include <kernel/yosys.h>

#include "emap/serialization.h"


namespace Yosys {

struct WriteStrataPass : public Pass {
public:
    WriteStrataPass() : Pass("write_strata", "write Strata IR to a file") {}

    void execute(std::vector<std::string> args, RTLIL::Design *design) override {
        if (args.size() < 2 || args.size() > 3) {
            log_error("Usage: write_strata <module_name> [<filename>]\n");
        }

        bool to_file = args.size() == 3;
        std::ostream* output_stream = to_file ? new std::ofstream(args[2]) : &std::cout;
        if (!output_stream->good()) {
            log_error("Could not open output stream.\n");
        }
        else {
            auto module = design->module("\\" + args[1]);
            if (!module) {
                log_error("Module '%s' not found in design.\n", args[1].c_str());
            }
            else {
                *output_stream << Yosys::Json(emap::serialization::serialize(module)).dump();
            }
        }
        if (to_file) {
            delete output_stream;
        }
    }
} write_strata_pass;

}
