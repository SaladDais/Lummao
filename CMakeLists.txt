cmake_minimum_required(VERSION 3.8)
project(Lummao LANGUAGES CXX)

include(GNUInstallDirs)

if (MSVC)
  # MSVC requires C++20 be enabled to allow designated initializers
  set(CMAKE_CXX_STANDARD 20)
else()
  set(CMAKE_CXX_STANDARD 17)
endif()
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(_IGNORED "${CMAKE_C_COMPILER}")

if (MSVC)
  # So?
  add_definitions("-D_CRT_SECURE_NO_WARNINGS=1")
else()
  add_definitions("-Wall -Wno-overloaded-virtual")
  if (NOT CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    add_definitions("-Wno-unneeded-internal-declaration")
  endif()
endif()

add_executable(lummao src/lummao.cc)
target_link_libraries(lummao PUBLIC ${EXTRA_LIBS} tailslide)
set_target_properties(lummao PROPERTIES OUTPUT_NAME lummao)
install(TARGETS lummao DESTINATION bin)
