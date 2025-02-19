#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
#

# This file is temporarly a tweaked version of the o3de's root CMakeLists.txt
# Once we have the install step, this file will be generated and wont require adding subdirectories

include(FindPackageHandleStandardArgs)

function(o3de_current_file_path path)
    set(${path} ${CMAKE_CURRENT_FUNCTION_LIST_DIR} PARENT_SCOPE)
endfunction()

o3de_current_file_path(current_path)

# Make sure we are matching LY_ENGINE_NAME_TO_USE with the current engine
file(READ ${current_path}/../engine.json engine_json)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${current_path}/../engine.json)

string(JSON this_engine_name ERROR_VARIABLE json_error GET ${engine_json} engine_name)
if(json_error)
    message(FATAL_ERROR "Unable to read key 'engine_name' from '${current_path}/../engine.json', error: ${json_error}")
endif()

set(found_matching_engine FALSE)
if(this_engine_name STREQUAL LY_ENGINE_NAME_TO_USE)
    set(found_matching_engine TRUE)
endif()

find_package_handle_standard_args(o3de
        "Could not find an engine with matching ${LY_ENGINE_NAME_TO_USE}"
        found_matching_engine
)

macro(o3de_initialize)
    set(INSTALLED_ENGINE FALSE)
    set(LY_PROJECTS ${CMAKE_CURRENT_LIST_DIR})
    o3de_current_file_path(current_path)
    add_subdirectory(${current_path}/.. o3de)
endmacro()