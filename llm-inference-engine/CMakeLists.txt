cmake_minimum_required(VERSION 3.15)
project(llm-engine VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Compiler warnings
if(MSVC)
    add_compile_options(/W4 /WX)
else()
    add_compile_options(-Wall -Wextra -Werror)
endif()

add_compile_definitions(LLM_ENGINE_RUNTIME_VERSION="${PROJECT_VERSION}")

# Find required packages
find_package(Threads REQUIRED)

# Source files
file(GLOB_RECURSE ENGINE_SOURCES CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp"
)

file(GLOB_RECURSE HEADERS CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/src/*.h"
)

list(FILTER ENGINE_SOURCES EXCLUDE REGEX ".*/src/main\\.cpp$")

add_library(llm-engine-core STATIC ${ENGINE_SOURCES} ${HEADERS})
target_include_directories(llm-engine-core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_link_libraries(llm-engine-core PRIVATE Threads::Threads)

# Main executable
add_executable(llm-engine src/main.cpp)

target_include_directories(llm-engine PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_link_libraries(llm-engine PRIVATE llm-engine-core Threads::Threads)

# Test executable
file(GLOB TEST_SOURCES CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/tests/*.cpp"
)

list(APPEND TEST_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_proof_surface.cpp"
)
list(REMOVE_DUPLICATES TEST_SOURCES)

add_executable(llm-engine-tests ${TEST_SOURCES})

target_link_libraries(llm-engine-tests PRIVATE llm-engine-core Threads::Threads)

enable_testing()
add_test(NAME unit_tests COMMAND llm-engine-tests --unit)
add_test(NAME backend_comparison COMMAND llm-engine-tests --backend-comparison)
add_test(NAME integration_tests COMMAND llm-engine-tests --integration)
