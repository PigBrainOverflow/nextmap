#include <iostream>
#include <kernel/yosys.h>
#include <kernel/yosys_common.h>
#include <kernel/functional.h>

#include "emap/utils.h"


namespace Yosys {

struct WriteFunctionalPass : public Pass {
public:
    WriteFunctionalPass() : Pass("write_functional", "convert module to Functional IR and write to file") {}

    void execute(std::vector<std::string> args, RTLIL::Design *design) override {
        if (args.size() < 2 || args.size() > 3) {
            log_error("Usage: write_functional <module_name> [<filename>]\n");
        }

        bool to_file = args.size() == 3;
        std::ostream* output_stream = to_file ? new std::ofstream(args[2]) : &std::cout;
        if (!output_stream->good()) {
            log_error("Could not open output stream.\n");
        }
        else {
            auto module = design->module(args[1]);
            if (!module) {
                log_error("Module '%s' not found in design.\n", args[1].c_str());
            }
            else {
                
            }
        }
        if (to_file) {
            delete output_stream;
        }
    }
};

}


USING_YOSYS_NAMESPACE
PRIVATE_NAMESPACE_BEGIN

class PrintVisitor : public Functional::DefaultVisitor<void> {
public:
    PrintVisitor(std::ostream &os) : os(os) {}
    virtual void default_handler(Functional::Node self) override {
        os << "Node: " << self.to_string() << std::endl;
    }
    virtual void buf(Functional::Node self, Functional::Node) override {
        os << "Buf: " << self.to_string() << self.name().c_str() << self.width() << std::endl;
    }

private:
    std::ostream &os;
};

struct MyPass : public Pass {
    MyPass() : Pass("my_cmd", "just a simple test") { }
    void execute(std::vector<std::string> args, RTLIL::Design *design) override
    {
        UNUSED(args);
        Functional::Writer writer(std::cout);
        PrintVisitor visitor(std::cout);
        for (auto mod : design->modules()) {
            std::cout << "Module: " << mod->name.c_str() << std::endl;
            auto fmod = Functional::IR::from_module(mod);
            for (const auto& node : fmod) {
                node.visit(visitor);
            }
            for (const auto& input : fmod.all_inputs()) {
                writer.print("Input: %s (%s)\n", input->name.c_str(), input->kind.c_str());
            }
            for (const auto& output : fmod.all_outputs()) {
                writer.print("Output: %s (%s)\n", output->name.c_str(), output->kind.c_str());
            }
        }
    }
} MyPass;


PRIVATE_NAMESPACE_END