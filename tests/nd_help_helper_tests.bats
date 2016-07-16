#!/usr/bin/env bats

load test_helpers

setup() {
    _shared_setup
}

@test "evaluating 'nd _help-helper <help text>' prints the help text and exits successfully when '--help' is the first argument" {
    make_executable_command nd-my-command <<- 'EOF'
		#!/bin/bash
		eval "$(nd _help-helper "My help message")"
		exit 1
EOF

    run nd my-command --help
    [[ $output = "My help message" ]]
    [[ $status = 0 ]]
}

@test "evaluating 'nd _help-helper' has no effect when --help is not the first argument" {
    _setup_test_directory

    make_executable_command nd-my-command <<- 'EOF'
		#!/bin/bash
		eval "$(nd _help-helper "My help message")"
		echo "My command output"
EOF

    run nd my-command
    [[ $output = "My command output" ]]
    [[ $status = 0 ]]
}

@test "'nd _help-helper --help' prints help" {
    run nd _help-helper --help
    [[ $output = *"usage"* ]]
    [[ $status = 0 ]]
}

@test "'nd help' includes description of _help-helper' " {
    run nd help
    [[ $output = *"Bash helper"* ]]
    [[ $status = 0 ]]
}
