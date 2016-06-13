#!/usr/bin/env bats

_setup_test_directory() {
    TEST_DIRECTORY="$(mktemp -d nd-toolbelt_test.XXXXX --tmpdir)"
    _append_to_exit_trap "rm -rf $TEST_DIRECTORY"
    PATH=$TEST_DIRECTORY:$PATH
}

_append_to_exit_trap() {
    # Makes sure to run the existing exit handler
    trap "$1; $(trap -p EXIT | awk '{print $3}')" EXIT
}

@test "'nd version' matches 'nd-version'" {
    actual="$(nd version)"
    expected="$(nd-version)"
    [[ "$actual" = "$expected" && -n "$actual" ]]
}

@test "'nd init -' returns 0 exit code" {
    actual="$(nd init -)"
    expected="$(cat nd_toolbelt/nd-init.sh)"    # TODO(hramos): Make not relative path?
    [[ "$actual" = "$expected" && -n "$expected" ]]
}

@test "'nd <command>' runs 'nd-<command>'" {
    _setup_test_directory

    echo "#!/usr/bin/env bash" > $TEST_DIRECTORY/nd-command-test
    echo "echo \$*" >> $TEST_DIRECTORY/nd-command-test
    chmod +x $TEST_DIRECTORY/nd-command-test

    result="$(nd command-test -a -b -c --f test)"
    [[ "$result" = "-a -b -c --f test" ]]
}

@test "nd autocomplete function returns matches that begin with nd" {
    _setup_test_directory

    touch $TEST_DIRECTORY/nd-toolbelt-random-unit-test-file
    chmod +x $TEST_DIRECTORY/nd-toolbelt-random-unit-test-file

    COMP_WORDS=("toolbelt-random-unit-test-")
    COMP_CWORD=0

    eval "$(nd init -)"
    _ndtoolbelt_autocomplete_hook

    [[ "toolbelt-random-unit-test-file" = "${COMPREPLY[0]}" ]]
}

@test "nd toolbelt does not autocomplete aliases" {
    _setup_test_directory

    alias nd-some-test-command="echo test"

    COMP_WORDS=("some-test-com")
    COMP_CWORD=0

    eval "$(nd init -)"
    _ndtoolbelt_autocomplete_hook
    [ -z "$COMPREPLY" ]

    # Verifies this test is setup correctly.
    unalias nd-some-test-command
    touch $TEST_DIRECTORY/nd-some-test-command
    chmod +x $TEST_DIRECTORY/nd-some-test-command

    _ndtoolbelt_autocomplete_hook
    [ -n "$COMPREPLY" ]
}

@test "nd toolbelt does not autocomplete functions" {
    _setup_test_directory
    nd-some-test-commmand() { true; }

    COMP_WORDS=("some-test-com")
    COMP_CWORD=0

    eval "$(nd init -)"
    _ndtoolbelt_autocomplete_hook
    [ -z "$COMPREPLY" ]

    # Verifies this test is setup correctly.
    touch $TEST_DIRECTORY/nd-some-test-command
    chmod +x $TEST_DIRECTORY/nd-some-test-command

    _ndtoolbelt_autocomplete_hook
    [ -n "$COMPREPLY" ]
}
