PROGRAM_PREFIX :=
YOSYS ?= yosys

# Plugin name
PLUGIN_NAME = nextmap_plugin_simple

.PHONY: all clean install test

all: $(PLUGIN_NAME).so

# Get Yosys build configuration
YOSYS_CONFIG = $(shell $(YOSYS)-config --cxxflags)
LDFLAGS = $(shell $(YOSYS)-config --ldflags)
LDLIBS = $(shell $(YOSYS)-config --ldlibs)

# Try to find Yosys source directory dynamically
YOSYS_BIN_DIR = $(shell dirname `which $(YOSYS)`)
YOSYS_SRC_DIR ?= $(shell \
	if [ -f "$(YOSYS_BIN_DIR)/../share/yosys/include/kernel/yosys.h" ]; then \
		echo "$(YOSYS_BIN_DIR)/.."; \
	elif [ -f "$(YOSYS_BIN_DIR)/kernel/yosys.h" ]; then \
		echo "$(YOSYS_BIN_DIR)"; \
	elif [ -n "$$YOSYS_SRC" ]; then \
		echo "$$YOSYS_SRC"; \
	else \
		echo ""; \
	fi)

# Add Yosys source directory if found, otherwise rely on yosys-config
ifneq ($(YOSYS_SRC_DIR),)
CXXFLAGS = $(YOSYS_CONFIG) -I$(YOSYS_SRC_DIR)
else
CXXFLAGS = $(YOSYS_CONFIG)
endif

# Build the plugin (no Python embedding needed)
$(PLUGIN_NAME).so: $(PLUGIN_NAME).cc
	$(CXX) $(CXXFLAGS) $(LDFLAGS) \
		-shared -fPIC -o $@ $< $(LDLIBS)

# Install plugin to Yosys plugin directory
install: $(PLUGIN_NAME).so
	mkdir -p $(shell $(YOSYS)-config --datdir)/plugins
	cp $(PLUGIN_NAME).so $(shell $(YOSYS)-config --datdir)/plugins/

# Test the plugin
test: $(PLUGIN_NAME).so
	@echo "Testing nextmap plugin..."
	$(YOSYS) -m ./$(PLUGIN_NAME).so -p 'help nextmap'

# Clean build artifacts
clean:
	rm -f *.so *.o *.d

# Show configuration
config:
	@echo "YOSYS: $(YOSYS)"
	@echo "YOSYS_BIN_DIR: $(YOSYS_BIN_DIR)"
	@echo "YOSYS_SRC_DIR: $(YOSYS_SRC_DIR)"
	@echo "CXXFLAGS: $(CXXFLAGS)"
	@echo "LDFLAGS: $(LDFLAGS)"
	@echo "LDLIBS: $(LDLIBS)"
