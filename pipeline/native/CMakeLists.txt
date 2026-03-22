cmake_minimum_required(VERSION 3.24)
project(fastgeo LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

find_package(Python 3.11 REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(fastgeo
    bindings.cpp
    fastgeo/geo.cpp
    fastgeo/simhash.cpp
)

target_include_directories(fastgeo PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

# -ffp-contract=off is required for parity with the Python reference: without
# it, Clang/GCC on FMA-capable hardware (e.g. Apple Silicon) may fuse
# multiply-add/subtract chains (as in the point-in-polygon cross-product and
# ray-intersection formulas) into a single rounding step, which can disagree
# in the last bit with Python's strictly-separate IEEE754 operations right on
# polygon boundaries. MSVC does not contract by default, so it needs no flag.
target_compile_options(fastgeo PRIVATE
    $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-O3 -Wall -Wextra -ffp-contract=off>
    $<$<CXX_COMPILER_ID:MSVC>:/O2 /W4>
)

# scikit-build-core installs this straight into the wheel root so
# `import fastgeo` finds it as a top-level extension module (no wrapper
# Python package needed).
install(TARGETS fastgeo LIBRARY DESTINATION .)
