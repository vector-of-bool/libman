## This module defines a libman-compliant importer for CMake, all through the
## `import_packages()` function (defined at the bottom of this file)
##
## This module does some trickery to increase performance, mainly by reducing
## the frequency with which we must read the libman manifests using timestamp
## checking based on "cache" files, wherein the content of a libman manifest
## is converted to a roughly equivalent CMake file that is directly include()'d
## to get the data.
##
## For example, when we wish to read the libman index, we generate a unique and
## deterministic destination for a .cmake file based on the hash of the filepath
## of the index. This file is the "index cache."
##
## (This file has nothing to do with the CMakeCache.txt format, although we
##  may wish to someday further optimize via some `load_cache()` trickery.)
##
## The "cache files" set global properties with information that was contained
## in the original libman manifest. The cache files for libraries will also
## define the imported targets to which a user will link.
##
## In addition, the cache files are generated as-needed, so there is no need to
## fear generating an enormous index.
##
##
## The cache file for the libman index sets the following properties:
##
## - libman_PACKAGES : A list of the packages which the index provides
## - libman_PACKAGES/<name>::Path : The path to the .lmp file for the <name>
##      package. Each package receives a global property of this format
##
##
## The cache file for packages (.lmp files) set the following properties:
##
## - libman_PACKAGES/<name>::Namepsace : The package 'Namespace' field
## - libman_PACKAGES/<name>::Requires : List of packages that must be imported
## - libman_PACKAGES/<name>::Libraries : List of the paths to `.lml` files
## - libman_PACKAGES/<name>::_Imported : Not from the manifest. FALSE until
##      the import finishes. Used to aide in dependency resolution for Requires
##
##
## The cache file for libraries (.lml files) does not set any properties, but
## instead creates the import targets for the libraries of the package.


# A variable to note the path to this file
set(LIBMAN_CMAKE_SCRIPT "${CMAKE_CURRENT_LIST_FILE}")

if(NOT CMAKE_SCRIPT_MODE_FILE)
    define_property(TARGET
        PROPERTY libman_EXPORT_PROPERTIES
        INHERITED
        BRIEF_DOCS "Properties to export in the libman file"
        FULL_DOCS "This adds X-CMake-Property lines to the libman library manifest for each property listed."
        )
    set_property(DIRECTORY PROPERTY libman_EXPORT_PROPERTIES "")
endif()

## Rewrites a path to be absolute, based on the directory containing `filepath`
# NOTE: `filepath` is a _file_ path, not a directory path. The filename will be
# stripped to get the containing directory.
function(_lm_resolve_path_from_file path_var filepath)
    # If it is already absolute, nothing to do.
    if(IS_ABSOLUTE "${${path_var}}")
        return()
    endif()
    # Get the directory containg `filepath`, and resolve the given path var
    # as being relative to that directory.
    get_filename_component(dirname "${filepath}" DIRECTORY)
    get_filename_component(abspath "${dirname}/${${path_var}}" ABSOLUTE)
    set(${path_var} "${abspath}" PARENT_SCOPE)
endfunction()


## Parse a libman-format manifest file, given a prefix and a path to a file to
## parse.
##
## All of the keys within the file create variables in the caller scope of the
## format <prefix>__<key>. The variable <prefix> is set to the list of keys
## that were parsed, allowing key iteration.
function(_lm_parse_file prefix filepath)
    file(READ "${filepath}" content)
    # Escape ';' in the file to prevent individual lines from splitting
    string(REPLACE ";" "\\;" content "${content}")
    # And now split the lines
    string(REPLACE "\n" ";" lines "${content}")
    # We read the file, so we depend on it
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${filepath}")
    # Clear the value of the prefix var
    set(${prefix})
    # Iterate the lines are parse each one
    foreach(line IN LISTS lines)
        # Whitespace is not significant
        string(STRIP "${line}" line)
        # Skip empty lines and comment lines
        if(line STREQUAL "" OR line MATCHES "^#")
            continue()
        endif()
        # Parse the key-value pairs
        if(NOT line MATCHES "^([^ \t]+):[ \t]+(.*)$")
            # It may be a key and value ^
            # ... or a key with an empty string:
            if(NOT line MATCHES "^([^ \t]):()$")
                message(WARNING "Invalid line in ${filepath}: ${line}")
                continue()
            endif()
        endif()
        # Strip the key and value in addition to the line to eat whitespace
        # around the ':'
        string(STRIP "${CMAKE_MATCH_1}" key)
        string(STRIP "${CMAKE_MATCH_2}" val)
        if(NOT key IN_LIST ${prefix})
            set(${prefix}__${key})
            list(APPEND ${prefix} "${key}")
        endif()
        # Escape the semicolon in the value to keep it as a single list item
        string(REPLACE ";" "\\;" val "${val}")
        list(APPEND ${prefix}__${key} "${val}")
    endforeach()
    # Send our parse result to the parent
    set(${prefix} "${${prefix}}" PARENT_SCOPE)
    foreach(key IN LISTS ${prefix})
        set(${prefix}__${key} "${${prefix}__${key}}" PARENT_SCOPE)
    endforeach()
endfunction()


## Import the library from the .lml file at `lib_path`, within the given `pkg`,
## with a name qualified with `namespace`.
function(_lm_import_lib pkg namespace lib_path)
    # Hash the filepath to get a unique ID for the actual import file.
    string(MD5 lib_path_hash "${lib_path}")
    string(SUBSTRING "${lib_path_hash}" 0 6 lib_path_hash)
    # Also use the stem from the original path so that we have something that's
    # actually readable in the file browser
    get_filename_component(stem "${lib_path}" NAME_WE)
    set(lib_cmake_file "${__lm_cache_dir}/pkgs/${pkg}/${stem}-${lib_path_hash}.cmake")
    # Generate the file only if it doesn't exist, or is older than the
    # .lml file being imported from.
    if("${lib_path}" IS_NEWER_THAN "${lib_cmake_file}")
        _lm_parse_file(lib "${lib_path}")
        if(NOT lib__Type STREQUAL "Library")
            message(WARNING "Wrong type for library file (${lib_path}): '${lib__Type}'")
        endif()
        if(NOT lib__Name)
            message(FATAL_ERROR "Library file did not provide a name: ${lib_path}")
        endif()
        # The header
        file(WRITE
            "${lib_cmake_file}.tmp"
            "## DO NOT EDIT.\n"
            "# This file was generated by libman from ${lib_path}\n\n"
            "# This file defines the import for '${lib__Name}' from ${pkg}\n"
            )
        # Detemine the linkage type
        if(lib__Path MATCHES "${CMAKE_STATIC_LIBRARY_SUFFIX}$")
            set(linkage STATIC)
        elseif(lib__Path MATCHES "${CMAKE_SHARED_LIBRARY_SUFFIX}$")
            set(linkage SHARED)
        elseif(lib__Path)
            message(WARNING "We don't recognize the type of import library: ${lib__Path}")
            set(linkage UNKNOWN)
        else()
            set(linkage INTERFACE)
        endif()
        # Create the add_library() call
        set(target_name "${namespace}::${lib__Name}")
        file(APPEND
            "${lib_cmake_file}.tmp"
            "add_library([[${target_name}]] IMPORTED ${linkage})\n"
            "set_property(TARGET [[${target_name}]] PROPERTY libman_OWNING_PACKAGE ${pkg})\n"
            "set_property(TARGET [[${target_name}]] PROPERTY libman_QUALIFIED_NAME ${namespace}/${lib__Name})\n\n"
            )
        # Set the import location, if applicable
        if(lib__Path)
            _lm_resolve_path_from_file(lib__Path "${lib_path}")
            file(APPEND
                "${lib_cmake_file}.tmp"
                "# Set the linkable file for the target\n"
                "set_property(TARGET [[${target_name}]] PROPERTY IMPORTED_LOCATION [[${lib__Path}]])\n\n"
                )
        endif()
        # Add the include directories
        foreach(inc IN LISTS lib__Include-Path)
            _lm_resolve_path_from_file(inc "${lib_path}")
            file(APPEND
                "${lib_cmake_file}.tmp"
                "set_property(TARGET [[${target_name}]] APPEND PROPERTY INTERFACE_INCLUDE_DIRECTORIES [[${inc}]])\n"
                )
        endforeach()
        # Add the preprocessor definitions (yuck)
        foreach(def IN LISTS lib__Preprocessor-Define)
            file(APPEND
                "${lib_cmake_file}.tmp"
                "set_property(TARGET [[${target_name}]] APPEND PROPERTY INTERFACE_COMPILE_DEFINITIONS [[${def}]])\n"
                )
        endforeach()
        # Add the transitive usage information (interface links)
        foreach(use IN LISTS lib__Uses lib__Links)
            if(NOT use MATCHES "^(.+)/(.+)$")
                message(FATAL_ERROR "Cannot resolve invalid transitive usage on ${target_name}: ${use}")
                continue()
            endif()
            set(use_ns "${CMAKE_MATCH_1}")
            set(use_lib "${CMAKE_MATCH_2}")
            file(APPEND
                "${lib_cmake_file}.tmp"
                "set_property(TARGET [[${target_name}]] APPEND PROPERTY INTERFACE_LINK_LIBRARIES [[${use_ns}::${use_lib}]])\n"
                )
        endforeach()
        # Add verbatim links
        foreach(link IN LISTS lib__X-CMake-Link)
            file(APPEND
                "${lib_cmake_file}.tmp"
                "set_property(TARGET [[${target_name}]] APPEND PROPERTY INTERFACE_LINK_LIBRARIES [[${link}]])\n"
                )
        endforeach()
        # Add special requirements
        foreach(req IN LISTS Lib__Special-Uses)
            if(req STREQUAL "Threading")
                file(APPEND
                    "${lib_cmake_file}.tmp"
                    "set_property(TARGET [[${target_name}]] APPEND PROPERTY INTERFACE_LINK_LIBRARIES [[Threads::Threads]])\n"
                    )
            else()
                message(WARNING "Un-implemented special requirement '${req}' for imported target '${target_name}'")
            endif()
        endforeach()
        # Commit
        file(RENAME "${lib_cmake_file}.tmp" "${lib_cmake_file}")
    endif()
    # Include the generated file, thereby defining the imported target. This is
    # where the magic happens!
    include("${lib_cmake_file}")
endfunction()


## Load the information about the package `name` from the already-loaded index.
function(_lm_load_package name)
    # Check that the index actually provides the package we asked for
    get_cmake_property(packages libman_PACKAGES)
    if(NOT name IN_LIST packages)
        message(FATAL_ERROR "Cannot import package '${name}': It is not named in the package index")
    endif()
    # Compute the destination for the cache file
    get_cmake_property(pkg_file libman_PACKAGES/${name}::path)
    set(pkg_cmake_file "${__lm_cache_dir}/pkgs/${name}.cmake")
    # Only generate it if it doesn't exist, or is out-of-date from the .lmp file
    if("${pkg_file}" IS_NEWER_THAN "${pkg_cmake_file}")
        _lm_parse_file(pkg "${pkg_file}")
        if(NOT pkg__Type STREQUAL "Package")
            message(WARNING "Wrong type for package file (${pkg_file}): '${pkg__Type}'")
        endif()
        if(NOT pkg__Name STREQUAL name)
            message(WARNING "Package's declared name does not match its name in the index: '${pkg__Name}' (Expected '${name}')")
        endif()
        if(pkg__Namespace STREQUAL "")
            message(FATAL_ERROR "Package '${pkg__Name}' does not declare a package namespace.")
        endif()
        # The header.
        # NOTE: We need to write empty strings for all of the array properties,
        # otherwise a call to get_property on that property will return NOTFOUND
        # in the case that the array property was never APPENDed to. This might
        # be fixable with define_property()?
        file(WRITE
            "${pkg_cmake_file}.tmp"
            "## DO NOT EDIT.\n"
            "# This file was generated by libman from ${pkg_file}\n"
            "set_property(GLOBAL PROPERTY [[libman_PACKAGES/${name}::Namespace]] [[${pkg__Namespace}]])\n"
            "set_property(GLOBAL PROPERTY [[libman_PACKAGES/${name}::Requires]] [[]])\n"
            "set_property(GLOBAL PROPERTY [[libman_PACKAGES/${name}::Libraries]] [[]])\n"
            "set_property(GLOBAL PROPERTY [[libman_PACKAGES/${name}::_Imported]] FALSE)\n"
            )
        # Expose the requirements
        foreach(req IN LISTS pkg__Requires)
            file(APPEND
                "${pkg_cmake_file}.tmp"
                "set_property(GLOBAL APPEND PROPERTY [[libman_PACKAGES/${name}::Requires]] [[${req}]])\n"
                )
        endforeach()
        # Set the path to the .lml files for the package
        foreach(lib IN LISTS pkg__Library)
            _lm_resolve_path_from_file(lib "${pkg_file}")
            file(APPEND
                "${pkg_cmake_file}.tmp"
                "set_property(GLOBAL APPEND PROPERTY [[libman_PACKAGES/${name}::Libraries]] [[${lib}]])\n"
                )
        endforeach()
        # Commit
        file(RENAME "${pkg_cmake_file}.tmp" "${pkg_cmake_file}")
    endif()
    # Include the generated file to set all the global properties
    include("${pkg_cmake_file}")
endfunction()


## Load up the index from LIBMAN_INDEX
function(_lm_load_index)
    # We haven't loaded the package cache yet (for the current LIBMAN_INDEX)
    set(index_file "${__lm_cache_dir}/index.cmake")
    # Check if the libman index is newer than the cache file:
    if("${LIBMAN_INDEX}" IS_NEWER_THAN "${index_file}")
        # Our cache needs updating
        _lm_parse_file(index "${LIBMAN_INDEX}")
        if(NOT index__Type STREQUAL "Index")
            message(SEND_ERROR "Non-index file set for LIBMAN_INDEX: ${LIBMAN_INDEX} (Type: ${index__Type})")
            return()
        endif()
        # Write a header
        file(WRITE
            "${index_file}.tmp"
            "## DO NOT EDIT.\n"
            "## This file is generated by libman.cmake to cache the result of the parseing of ${LIBMAN_INDEX}.\n"
            "set_property(GLOBAL PROPERTY libman_PACKAGES [[]])\n\n"
            )
        # Declare the packages
        foreach(pkg IN LISTS index__Package)
            if(NOT pkg MATCHES "^([^;]+);([^;]+)$")
                message(FATAL_ERROR "Invalid 'Package' entry in index: ${pkg}")
                continue()
            endif()
            # Strip whitespace from the keys around the ';'
            string(STRIP "${CMAKE_MATCH_1}" name)
            string(STRIP "${CMAKE_MATCH_2}" path)
            # Resolve the path to the .lmp
            _lm_resolve_path_from_file(path "${LIBMAN_INDEX}")
            file(APPEND
                "${index_file}.tmp"
                "# Package '${name}'\n"
                "set_property(GLOBAL APPEND PROPERTY libman_PACKAGES ${name})\n"
                "set_property(GLOBAL PROPERTY [[libman_PACKAGES/${name}::path]] [[${path}]])\n\n"
                )
        endforeach()
        # Commit
        file(RENAME "${index_file}.tmp" "${index_file}")
    endif()
    # Load the index
    include("${index_file}")
endfunction()


## "Import" the given pakage. Different from loading, in that it will also
## import the libraries from the package (and its dependencies)
function(_lm_import_package name)
    # Don't pass over a package twice.
    get_cmake_property(already_imported libman_PACKAGES/${name}::_Imported)
    if(already_imported)
        return()
    endif()
    # Load the package data from the index
    _lm_load_package("${name}")
    # Import the requirements of the package
    get_cmake_property(reqs libman_PACKAGES/${name}::Requires)
    foreach(req IN LISTS reqs)
        _lm_import_package(${req})
    endforeach()
    # Define the import libraries
    get_cmake_property(namespace libman_PACKAGES/${name}::Namespace)
    get_cmake_property(libs libman_PACKAGES/${name}::Libraries)
    foreach(lib IN LISTS libs)
        _lm_import_lib("${name}" "${namespace}" "${lib}")
    endforeach()
    # Remember that we've already imported this package.
    set_property(GLOBAL PROPERTY libman_PACKAGES/${name}::_Imported TRUE)
endfunction()


## The only public interface for libman! Name your packages, and we'll import
## them! You _must_ set the `LIBMAN_INDEX` variable to a path to the libman
## index. Recommended to let a dependency manager do this for you.
function(import_packages)
    set(looked_for)
    if(NOT DEFINED LIBMAN_INDEX)
        foreach(cand
                CMAKE_CURRENT_BINARY_DIR
                PROJECT_BINARY_DIR
                CMAKE_BINARY_DIR
                CMAKE_CURRENT_SOURCE_DIR
                PROJECT_SOURCE_DIR
                CMAKE_SOURCE_DIR
                )
            set(cand "${${cand}}/INDEX.lmi")
            list(APPEND looked_for "${cand}")
            if(EXISTS "${cand}")
                set(LIBMAN_INDEX "${cand}")
            endif()
        endforeach()
    endif()
    if(NOT DEFINED LIBMAN_INDEX)
        list(REMOVE_DUPLICATES looked_for)
        string(REPLACE ";" ", " looked_for "${looked_for}")
        message(FATAL_ERROR "No LIBMAN_INDEX variable defined, and no INDEX.lmi was found (Looked for ${looked_for})")
    endif()
    get_filename_component(LIBMAN_INDEX "${LIBMAN_INDEX}" ABSOLUTE)
    # Get the location of our cached parse
    # Hash the index path to generate an in-build directory where we store the
    # cache files
    string(MD5 path_hash "${LIBMAN_INDEX}")
    string(SUBSTRING "${path_hash}" 0 6 __lm_index_path_hash)
    get_filename_component(__lm_cache_dir "${CMAKE_BINARY_DIR}/_libman-${__lm_index_path_hash}" ABSOLUTE)
    # Load up that index data into global properties
    _lm_load_index()
    # Now import those packages
    foreach(name IN LISTS ARGN)
        _lm_import_package("${name}")
    endforeach()
endfunction()


function(export_package)
    set(options
        ADD_TO_ALL
        )
    set(args
        NAMESPACE
        NAME
        )
    set(list_args
        REQUIRES
        )
    cmake_parse_arguments(PARSE_ARGV 0 ARG "${options}" "${args}" "${list_args}")

    foreach(arg IN LISTS ARG_UNPARSED_ARGUMENTS)
        message(SEND_ERROR "Unknown argument to export_package: ${arg}")
    endforeach()
    if(DEFINED ARG_UNPARSED_ARGUMENTS)
        message(FATAL_ERROR "Invalid arguments to export_package()")
    endif()

    if(NOT TARGET libman-export)
        add_custom_target(libman-export)
    endif()

    if(NOT ARG_NAME)
        set(ARG_NAME "${PROJECT_NAME}")
    endif()
    if(NOT ARG_NAMESPACE)
        set(ARG_NAMESPACE "${ARG_NAME}")
    endif()

    set(all_arg)
    if(ARG_ADD_TO_ALL)
        set(all_arg ALL)
    endif()

    set(target __libman-export-package-${ARG_NAME})
    if(TARGET "${target}")
        message(FATAL_ERROR "export_package() for ${ARG_NAME} called multiple times")
    endif()
    add_custom_target(${target} ${all_arg})
    add_dependencies(libman-export ${target})

    get_filename_component(__export_root "${CMAKE_BINARY_DIR}/${ARG_NAME}.libman-export" ABSOLUTE)
    set_target_properties("${target}" PROPERTIES
        EXPORT_ROOT "${__export_root}"
        NAMESPACE "${ARG_NAMESPACE}"
        REQUIRES "${ARG_REQUIRES}"
        )

    # Create the root directory for the export
    file(REMOVE_RECURSE "${__export_root}")

    # Generate the head of the file
    set(req_genex $<TARGET_PROPERTY:${target},REQUIRES>)
    set(has_requirements $<BOOL:${req_genex}>)
    set(req_list "$<JOIN:${req_genex},\nRequires: >")
    set(req_lines "$<${has_requirements}:Requires: ${req_list}>")
    set(lib_genex $<TARGET_PROPERTY:${target},LIBRARIES>)
    set(has_libraries $<BOOL:${lib_genex}>)
    set(lib_list "$<JOIN:${lib_genex},\nLibrary: >")
    set(lib_lines "$<${has_libraries}:Library: ${lib_list}>")
    string(CONFIGURE [[
# This file was generated by `export_package` from CMake for ${PROJECT_NAME} ${PROJECT_VERSION}
Type: Package
Name: ${ARG_NAME}
Namespace: ${ARG_NAMESPACE}
${req_lines}
${lib_lines}
]] lmp_content)
    set(_lm_dir "${CMAKE_CURRENT_BINARY_DIR}/_libman")
    set(__lmp_path_tmpl "${_lm_dir}/${ARG_NAME}.lmp.in")
    file(WRITE "${__lmp_path_tmpl}" "${lmp_content}")

    file(GENERATE OUTPUT "${__export_root}/${ARG_NAME}.lmp" INPUT "${__lmp_path_tmpl}")
endfunction()


function(_lm_target_name_genex out target)
    set(lm_name $<TARGET_PROPERTY:${target},LIBMAN_NAME>)
    set(output_name $<TARGET_PROPERTY:${target},OUTPUT_NAME>)
    set(default_name "$<IF:$<BOOL:${output_name}>,${output_name},${target}>")
    set(name_genex $<IF:$<BOOL:${lm_name}>,${lm_name},${default_name}>)
    set("${out}" "${name_genex}" PARENT_SCOPE)
endfunction()


function(export_library exp_target)
    set(options)
    set(args
        NAME
        PACKAGE
        )
    set(list_args
        HEADER_ROOTS
        HEADER_PATTERNS
        EXTRA_HEADER_PATTERNS
        )
    cmake_parse_arguments(PARSE_ARGV 0 ARG "${options}" "${args}" "${list_args}")

    # Fill in the header patterns we will be copying
    if(NOT ARG_HEADER_PATTERNS)
        set(ARG_HEADER_PATTERNS
            *.h
            *.hh
            *.hpp
            *.h++
            *.inc
            *.inl
            *.H
            *.tpp
            )
    endif()
    set(header_patterns ${ARG_HEADER_PATTERNS} ${ARG_EXTRA_HEADER_PATTERNS})

    # Default package name to the project name
    if(NOT ARG_PACKAGE)
        set(ARG_PACKAGE "${PROJECT_NAME}")
    endif()

    # Default the name to the target name
    if(NOT ARG_NAME)
        set(ARG_NAME "${exp_target}")
    endif()

    # Sanity checks on the caller
    if(NOT TARGET "${exp_target}")
        message(SEND_ERROR "export_library() requires a library target argument")
        return()
    endif()
    get_target_property(imported "${exp_target}" IMPORTED)
    if(imported)
        message(SEND_ERROR "Exporting an imported target ('${exp_target}') is not allowed")
        return()
    endif()
    get_target_property(type "${exp_target}" TYPE)
    set(path_genex)
    if(type MATCHES "^((STATIC|SHARED|MODULE)_LIBRARY)$")
        set(libdir lib)
        if(type MATCHES "^(SHARED|MODULE)" AND CMAKE_SHARED_LIBRARY_SUFFIX STREQUAL ".dll")
            # Main lib path goes in `bin/` for DLLs
            set(libdir bin)
        endif()
        set(path_genex ${libdir}/$<TARGET_FILE_NAME:${exp_target}>)
    elseif(type STREQUAL "OBJECT_LIBRARY")
        message(SEND_ERROR "Exporting of OBJECT libraries is not supported")
        return()
    elseif(type STREQUAL "EXECUTABLE")
        message(SEND_ERROR "Exporting of executables is not supported")
        return()
    endif()

    # Check that we are actually part of a real package
    set(pkg_target __libman-export-package-${ARG_PACKAGE})
    if(NOT TARGET "${pkg_target}")
        message(FATAL_ERROR "Cannot export library into non-existent package '${ARG_PACKAGE}' (did you call `export_package()` before `export_library`?) (Check the PACKAGE argument)")
    endif()

    # Generate the target that will do the export
    set(lm_target __libman-export-library-${ARG_NAME})
    if(TARGET "${lm_target}")
        message(FATAL_ERROR "Cannot generate an export for ${ARG_NAME} (Name is already exported)")
    endif()
    add_custom_target("${lm_target}")
    add_dependencies("${pkg_target}" "${lm_target}")
    # Temporary dir
    set(_lm_dir "${CMAKE_CURRENT_BINARY_DIR}/_libman")

    # Get properties from the package
    get_target_property(__export_root "${pkg_target}" EXPORT_ROOT)
    get_target_property(namespace "${pkg_target}" NAMESPACE)
    get_target_property(already_exported "${pkg_target}" EXPORTED_TARGETS)
    set(lib_infix "libs/${namespace}/${ARG_NAME}")
    set(lib_root "${__export_root}/${lib_infix}")

    # Add this library to the package listing
    set_property(
        TARGET "${pkg_target}"
        APPEND PROPERTY LIBRARIES
        "${lib_infix}/${ARG_NAME}.lml"
        )
    set_property(
        TARGET "${pkg_target}"
        APPEND PROPERTY EXPORTED_TARGETS
        ${exp_target}
    )

    # Generate targets which will install the headers into the export directory
    set(__has_headers FALSE)
    foreach(dir IN LISTS ARG_HEADER_ROOTS)
        set(__has_headers TRUE)
        get_filename_component(dir "${dir}" ABSOLUTE)
        string(MD5 dir_hash "${dir}")
        string(SUBSTRING "${dir_hash}" 0 6 dir_hash)
        set(stamp_file "${CMAKE_CURRENT_BINARY_DIR}/_libman/headers-${dir_hash}.stamp")
        set(existing_headers)
        foreach(pat IN LISTS header_patterns)
            file(GLOB_RECURSE more_headers CONFIGURE_DEPENDS "${dir}/${pat}")
            list(APPEND existing_headers ${more_headers})
        endforeach()
        add_custom_command(
            OUTPUT "${stamp_file}"
            DEPENDS ${ARG_HEADERS_DEPENDS} ${existing_headers}
            COMMAND "${CMAKE_COMMAND}"
                -D "__LIBMAN_INSTALL_HEADERS_MODE=TRUE"
                -D "HEADER_ROOT=${dir}"
                -D "PATTERNS=${header_patterns}"
                -D "DESTINATION=${lib_root}/include"
                -P "${LIBMAN_CMAKE_SCRIPT}"
            COMMAND "${CMAKE_COMMAND}" -E touch "${stamp_file}"
            COMMENT "Copying headers from ${dir} to libman export"
            VERBATIM
            )
        add_custom_target(libman-export-headers-${dir_hash} DEPENDS "${stamp_file}")
        add_dependencies("${lm_target}" libman-export-headers-${dir_hash})
    endforeach()

    # Generate a target that will copy the file to the export root
    set(stamp_file "${CMAKE_CURRENT_BINARY_DIR}/_libman/copy-${exp_target}.stamp")
    add_custom_command(
        OUTPUT "${stamp_file}"
        DEPENDS ${exp_target}
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${lib_root}/${libdir}"
        COMMAND "${CMAKE_COMMAND}" -E copy
            "$<TARGET_FILE:${exp_target}>"
            "${lib_root}/${libdir}/"
        COMMAND "${CMAKE_COMMAND}" -E touch "${stamp_file}"
        COMMENT "Copy library ${exp_target} to libman export root"
        )
    add_custom_target(__libman-export-copy-${exp_target} DEPENDS "${stamp_file}")
    add_dependencies(${lm_target} __libman-export-copy-${exp_target})

    # Get the export name of the library
    _lm_target_name_genex(name_to_write "${exp_target}")

    # Generate the library file head
    set(__lml_tmpl "${_lm_dir}/${target}.lml.in")
    file(WRITE "${__lml_tmpl}" "")
    file(APPEND "${__lml_tmpl}" "Type: Library\n")
    file(APPEND "${__lml_tmpl}" "Name: ${name_to_write}\n")
    if(__has_headers)
        file(APPEND "${__lml_tmpl}" "Include-Path: include\n")
    endif()

    # The path to the compiled binary
    if(path_genex)
        file(APPEND "${__lml_tmpl}" "Path: ${path_genex}\n")
    endif()

    # Export the compile definitions for the library
    set(defines "$<TARGET_PROPERTY:${exp_target},INTERFACE_COMPILE_DEFINITIONS>")
    set(def_join "$<JOIN:${defines},\nPreprocessor-Define: >")
    set(defines_line "$<$<BOOL:${defines}>:Preprocessor-Define: ${def_join}\n>")
    file(APPEND "${__lml_tmpl}" "${defines_line}")

    # The big one: Export the transitive usage requirements
    get_target_property(libs "${exp_target}" INTERFACE_LINK_LIBRARIES)
    if(libs STREQUAL "libs-NOTFOUND")
        set(libs)
    endif()
    set(required_by_usage)
    foreach(lib IN LISTS libs)
        if(lib MATCHES "^-")
            message(WARNING
                "export_package() for '${ARG_NAME}' exports target '${exp_target}', "
                "which uses link flag '${lib}'. This is not supported and will "
                "be omitted from the export information."
                )
            continue()
        endif()
        if(NOT TARGET "${lib}")
            message(WARNING
                "export_package() for '${ARG_NAME}' exports target '${exp_target}', "
                "which links to '${lib}', but '${lib}' is not a CMake target. "
                "It will be omitted from the export information."
                )
            continue()
        endif()
        get_target_property(lm_qual_name "${lib}" libman_QUALIFIED_NAME)
        get_target_property(lm_owning_package "${lib}" libman_OWNING_PACKAGE)
        get_target_property(lm_verbatim_link_ok "${lib}" libman_VERBATIM_LINK_OKAY)
        get_target_property(is_imported "${lib}" IMPORTED)
        if(TARGET "${lib}" AND NOT is_imported)
            if(NOT lib IN_LIST already_exported)
                message(WARNING
                    "export_library(${exp_target}): ${exp_target} links to CMake "
                    "target '${lib}', but '${lib}' is not already exported. "
                    "If you are exporting this target, place the export_library(${lib}) "
                    "call before the export_library(${exp_target}) call. If there "
                    "is no export_library(${lib}) call, THE GENERATED EXPORT WILL "
                    "BE UNUSABLE!"
                    )
            endif()
            _lm_target_name_genex(other_name "${lib}")
            file(APPEND "${__lml_tmpl}" "Uses: ${namespace}/${other_name}")
        elseif(lib STREQUAL "Threads::Threads")
            file(APPEND "${__lml_tmpl}" "Special-Uses: Threading\n")
        elseif(lib STREQUAL "std::filesystem")
            file(APPEND "${__lml_tmpl}" "Special-Uses: Filesystem\n")
        elseif(lm_qual_name)
            file(APPEND "${__lml_tmpl}" "Uses: ${lm_qual_name}\n")
            list(APPEND required_by_usage ${lm_owning_package})
            set(required_by_usage "${required_by_usage}" PARENT_SCOPE)
        elseif(is_imported)
            file(APPEND "${__lml_tmpl}" "X-CMake-Link: ${lib}\n")
            if(NOT lm_verbatim_link_ok)
                message(STATUS
                    "NOTE: Exported target '${exp_target}' links to '${lib}', which is "
                    "an imported library with no associated package information."
                    )
                message(STATUS
                    "NOTE: Downstream CMake projects which link to '${exp_target}' will "
                    "link to '${lib}' verbatim without dependency information."
                    )
            endif()
        else()
            message(WARNING
                "export_package() for '${ARG_NAME}' exports target '${exp_target}', "
                "which links to '${lib}', but '${lib}' is not a CMake target. "
                "It will be omitted from the export information."
                )
        endif()
    endforeach()

    get_target_property(export_props "${exp_target}" libman_EXPORT_PROPERTIES)
    foreach(compat_prop
            COMPATIBLE_INTERFACE_BOOL
            COMPATIBLE_INTERFACE_NUMBER_MAX
            COMPATIBLE_INTERFACE_NUMBER_MIN
            COMPATIBLE_INTERFACE_STRING
            )
        get_target_property(propval "${exp_target}" "${compat_prop}")
        if(NOT propval STREQUAL "propval-NOTFOUND")
            list(APPEND export_props ${propval})
        endif()
    endforeach()
    list(REMOVE_DUPLICATES export_props)
    foreach(prop IN LISTS export_props compat_string compat_bool compat_num_min compat_num_max)
        string(GENEX_STRIP "${prop}" wo_genex)
        if(NOT wo_genex STREQUAL prop)
            message(WARNING "libman_EXPORT_PROPERTIES does not support generator expressions (Found export of `${prop}`)")
            continue()
        endif()
        set(prop_genex "$<TARGET_PROPERTY:${exp_target},${prop}>")
        set(is_empty "$<STREQUAL:,${prop_genex}>")
        set(not_empty "$<NOT:${is_empty}>")
        file(APPEND "${__lml_tmpl}" "$<${not_empty}:X-CMake-Property: ${prop} := $<TARGET_PROPERTY:${exp_target},${prop}>\n>")
    endforeach()

    # Add the Requires fields to the package
    get_target_property(reqs "${pkg_target}" REQUIRES)
    list(APPEND reqs "${required_by_usage}")
    list(REMOVE_DUPLICATES reqs)
    set_property(TARGET "${pkg_target}" PROPERTY REQUIRES "${reqs}")

    # Generate the final lml file
    set(lml_path_genex "${lib_root}/${ARG_NAME}.lml")
    file(GENERATE
        OUTPUT "${lml_path_genex}"
        INPUT "${__lml_tmpl}"
        )
endfunction()


# Check if we are running in __LIBMAN_INSTALL_HEADERS_MODE
if(__LIBMAN_INSTALL_HEADERS_MODE)
    message(STATUS "Exporting headers from project based within '${HEADER_ROOT}'")
    set(pattern_args)
    foreach(pat IN LISTS PATTERNS)
        list(APPEND pattern_args PATTERN ${pat})
    endforeach()
    file(
        INSTALL "${HEADER_ROOT}/"
        DESTINATION "${DESTINATION}"
        USE_SOURCE_PERMISSIONS
        FILES_MATCHING ${pattern_args}
        )
    function(_prune_if_empty dirpath)
        if(IS_DIRECTORY "${dirpath}")
            file(GLOB children "${dirpath}/*")
            if(children STREQUAL "")
                message(STATUS "Remove empty directory: ${dirpath}")
                file(REMOVE "${dirpath}")
                get_filename_component(pardir "${dirpath}" DIRECTORY)
                _prune_if_empty("${pardir}")
            endif()
        endif()
    endfunction()
    message(STATUS "Pruning empty include subdirectories...")
    file(GLOB_RECURSE files "${DESTINATION}/*")
    file(GLOB_RECURSE dirs LIST_DIRECTORIES true "${DESTINATION}/*")
    list(REMOVE_ITEM dirs ${files})
    foreach(dir IN LISTS dirs)
        file(GLOB_RECURSE files "${dir}/*")
        # `files` will only contain files, not directories. If this dir has
        # any file children, the list will be non-empty
        if(files STREQUAL "")
            message(STATUS "Removing empty directory: ${dir}")
            file(REMOVE_RECURSE "${dir}")
        endif()
    endforeach()
    return()
endif()

# Define the threading interface lib, used for the `Threading` requirement
find_package(Threads)
