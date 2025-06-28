cmake_minimum_required(VERSION 3.10)

project(emap VERSION 0.0.0)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)   # generate compile_commands.json
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED YES)

# set the path to yosys-config if it's not in the PATH
set(YOSYS_CONFIG yosys-config)

execute_process(COMMAND ${YOSYS_CONFIG} --cxxflags OUTPUT_VARIABLE YOSYS_CXXFLAGS OUTPUT_STRIP_TRAILING_WHITESPACE)
separate_arguments(YOSYS_CXXFLAGS NATIVE_COMMAND "${YOSYS_CXXFLAGS}")
execute_process(COMMAND ${YOSYS_CONFIG} --ldflags OUTPUT_VARIABLE YOSYS_LDFLAGS OUTPUT_STRIP_TRAILING_WHITESPACE)
separate_arguments(YOSYS_LDFLAGS NATIVE_COMMAND "${YOSYS_LDFLAGS}")

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

file(GLOB_RECURSE SOURCES src/*.cpp)

add_library(emap SHARED ${SOURCES})
target_compile_options(emap PRIVATE ${YOSYS_CXXFLAGS})
target_link_libraries(
    emap PRIVATE
    ${YOSYS_LDFLAGS}
)
