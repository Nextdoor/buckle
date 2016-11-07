#!/usr/bin/env bats

load test_helpers

setup() {
    _shared_setup belt
}

@test "evaluating 'buckle _help-helper <help text>' prints the help text and exits successfully when '--help' is the first argument" {
    make_executable_command belt-my-command <<- 'EOF'
		#!/bin/bash
		eval "$(buckle _help-helper "My help message")"
EOF

    BUCKLE_TOOLBELT_NAME=belt run buckle my-command --help
    [[ $output = "My help message" ]]
    [[ $status = 0 ]]
}

@test "evaluating 'buck _help-helper' has no effect when --help is not the first argument" {
    _setup_test_directory

    make_executable_command belt-my-command <<- 'EOF'
		#!/bin/bash
		eval "$(buckle _help-helper "My help message")"
		echo "My command output"
EOF

    BUCKLE_TOOLBELT_NAME=belt run buckle my-command
    [[ $output = "My command output" ]]
    [[ $status = 0 ]]
}

@test "'buckle _help-helper --help' prints help" {
    BUCKLE_TOOLBELT_NAME=belt run buckle _help-helper --help
    [[ $output = *"usage"* ]]
    [[ $status = 0 ]]
}

@test "'buckle help' includes description of _help-helper' " {
    BUCKLE_TOOLBELT_NAME=belt run buckle help
    [[ $output = *"Bash helper"* ]]
    [[ $status = 0 ]]
}
