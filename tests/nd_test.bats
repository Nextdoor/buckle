#!/usr/bin/env bats

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
    test_directory="$(mktemp -d nd-toolbelt_test.XXXXX --tmpdir)"
    _append_to_exit_trap "rm -rf $test_directory"
    PATH=$test_directory:$PATH

    echo "#!/usr/bin/env bash" > $test_directory/nd-command-test
    echo "echo \$*" >> $test_directory/nd-command-test
    chmod +x $test_directory/nd-command-test

    result="$(nd command-test -a -b -c --f test)"
    [[ "$result" = "-a -b -c --f test" ]]
}

@test "nd autocomplete function returns matches that begin with nd" {
    test_directory="$(mktemp -d nd-toolbelt_test.XXXXX --tmpdir)"
    _append_to_exit_trap "rm -rf $test_directory"
    PATH=$test_directory:$PATH

    touch $test_directory/nd-toolbelt-random-unit-test-file
    chmod +x $test_directory/nd-toolbelt-random-unit-test-file

    COMP_WORDS=("toolbelt-random-unit-test-")
    COMP_CWORD=0

    eval "$(nd init -)"
    _ndtoolbelt_autocomplete_hook

    [[ "toolbelt-random-unit-test-file" = "${COMPREPLY[0]}" ]]
}
