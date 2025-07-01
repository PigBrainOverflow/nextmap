cmake_minimum_required(VERSION 3.10)

project(emap VERSION 0.0.0)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)   # generate compile_commands.json
# set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED YES)

set(YOSYS_BUILD_DIR "~/yosys/build")
set(YOSYS_INCLUDE_DIR "~/yosys")
set(YOSYS_CONFIG "${YOSYS_BUILD_DIR}/yosys-config")

execute_process(COMMAND bash -c "${YOSYS_CONFIG} --cxxflags" OUTPUT_VARIABLE YOSYS_CXXFLAGS OUTPUT_STRIP_TRAILING_WHITESPACE)
string(REGEX REPLACE "-I[^ ]+" "" YOSYS_CXXFLAGS "${YOSYS_CXXFLAGS}")   # ignore -I flags
separate_arguments(YOSYS_CXXFLAGS NATIVE_COMMAND "${YOSYS_CXXFLAGS}")

execute_process(COMMAND bash -c "${YOSYS_CONFIG} --ldflags" OUTPUT_VARIABLE YOSYS_LDFLAGS OUTPUT_STRIP_TRAILING_WHITESPACE)
separate_arguments(YOSYS_LDFLAGS NATIVE_COMMAND "${YOSYS_LDFLAGS}")

include_directories(
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
    "${YOSYS_INCLUDE_DIR}"
)

file(GLOB_RECURSE SRCS "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp")
file(GLOB YOSYS_OBJS "${YOSYS_BUILD_DIR}/kernel/*.o")

add_library(emap SHARED "${SRCS}")
target_compile_options(emap PRIVATE "${YOSYS_CXXFLAGS}")
target_link_libraries(
    emap PRIVATE
    "${YOSYS_LDFLAGS}"
    "${YOSYS_OBJS}"
)
