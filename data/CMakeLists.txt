if(BUILD_SPEC)
    if(NOT TARGET Bikeshed::Bikeshed)
        message(STATUS "No Bikeshed executable, so we will not generate the spec document")
    else()
        get_filename_component(bs_input "spec.bs" ABSOLUTE)
        get_filename_component(bs_html "${PROJECT_BINARY_DIR}/spec.html" ABSOLUTE)

        add_custom_command(
            OUTPUT "${bs_html}"
            DEPENDS "${bs_input}"
            COMMAND Bikeshed::Bikeshed spec "${bs_input}" "${bs_html}"
            COMMENT "Rendering specification to ${bs_html}"
            )
        add_custom_target(libman-spec DEPENDS "${bs_html}")
        add_custom_target(libman-spec-watch
            COMMAND Bikeshed::Bikeshed watch "${bs_input}" "${bs_html}"
            COMMENT "Watching ${bs_input} for changes"
            USES_TERMINAL
            )
    endif()
endif()
