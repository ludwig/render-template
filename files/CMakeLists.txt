# CMakeLists.txt

project(foobar)
cmake_minimum_required(VERSION 2.8)

# Set path for CMake dependencies
if (NOT CMAKE_MODULE_PATH)
    set(CMAKE_MODULE_PATH) # init to empty list
endif()
list(APPEND CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/config")

# Build list of common libraries (initialize to empty list)
set(COMMON_LIBRARIES)

# Decide whether to build the tests or not (default is 'false')
if(NOT DEFINED BUILD_TESTS)
    set(BUILD_TESTS FALSE)
endif()

# Set a default build type for single-configuration
if(NOT CMAKE_CONFIGURATION_TYPES AND NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE RelWithDebInfo)
endif()

# Select flags
set(CMAKE_CXX_FLAGS "-Wall -Wno-unused-variable")
set(CMAKE_CXX_FLAGS_RELWITHDEBINFO "-O2 -g")
set(CMAKE_CXX_FLAGS_RELEASE "-O2")
set(CMAKE_CXX_FLAGS_DEBUG "-O0 -g")

# -----------------------------------------------------------------------------

# Configure Boost
set(BOOST_USE_STATIC_LIBS ON)
set(BOOST_USE_MULTITHREADED ON)
set(REQUIRED_BOOST_VERSION 1.55)
find_package(Boost ${REQUIRED_BOOST_VERSION}
             COMPONENTS
             exception
             system
             thread
             serialization
             filesystem
             program_options
             REQUIRED
)
include_directories(${Boost_INCLUDE_DIR})
list(APPEND COMMON_LIBRARIES ${Boost_LIBRARIES})
message(STATUS "Boost settings:")
message(STATUS "  BOOST_ROOT = ${BOOST_ROOT}")

# Configure pkg-config (used for configuring other libraries: see "pkg-config --list-all")
find_package(PkgConfig)

# See also http://www.cmake.org/Wiki/CMake_Useful_Variables
message(STATUS "Other project settings:")
message(STATUS "  PROJECT_SOURCE_DIR = ${PROJECT_SOURCE_DIR}")
message(STATUS "  CMAKE_SYSTEM_NAME = ${CMAKE_SYSTEM_NAME}")

# -----------------------------------------------------------------------------

# Load build targets
include("targets.txt")

# Build libfoobar.a
include_directories("${PROJECT_SOURCE_DIR}/include")
add_library(foobar STATIC ${LIBFOO_SOURCES})

# Build stuff in "bin"
foreach(target ${BIN_TARGETS})
    add_executable(${target} "bin/${target}.cpp")
    target_link_libraries(${target} foobar ${COMMON_LIBRARIES})
endforeach()

# Build stuff in "tests"
if(BUILD_TESTS)
    foreach(target ${TEST_TARGETS})
        add_executable(${target} "tests/${target}.cpp")
        target_link_libraries(${target} foobar ${COMMON_LIBRARIES})
    endforeach()
endif()
# EOF
