cmake_minimum_required(VERSION 3.10)
project(emapcc)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)   # generate compile_commands.json
# add_compile_definitions(DEBUG)

# pybind11
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
find_package(pybind11 REQUIRED)

# sqlite3
find_package(SQLite3 REQUIRED)

include_directories(
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
    "${SQLite3_INCLUDE_DIRS}"
)
file(GLOB SRCS "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp")

pybind11_add_module(emapcc "${SRCS}")
target_link_libraries(emapcc PRIVATE SQLite::SQLite3)