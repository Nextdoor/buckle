#!/usr/bin/env bats

setup() {
    unset ND_TOOLBELT_ROOT
}

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

@test "'nd ' returns matches that begin with nd" {
    _setup_test_directory

    touch $TEST_DIRECTORY/nd-toolbelt-random-unit-test-file
    chmod +x $TEST_DIRECTORY/nd-toolbelt-random-unit-test-file

    COMP_WORDS=("nd" "toolbelt-random-unit-test-")
    COMP_CWORD=1

    eval "$(nd init -)"
    _ndtoolbelt_autocomplete_hook

    [[ "toolbelt-random-unit-test-file" = "${COMPREPLY[*]}" ]]
}

@test "'nd help' returns matches that begin with nd" {
    _setup_test_directory

    touch $TEST_DIRECTORY/nd-toolbelt-random-unit-test-file
    chmod +x $TEST_DIRECTORY/nd-toolbelt-random-unit-test-file

    COMP_WORDS=("nd" "help" "toolbelt-random-unit-test-file")
    COMP_CWORD=2

    eval "$(nd init -)"
    _ndtoolbelt_autocomplete_hook

    [[ "toolbelt-random-unit-test-file" = "${COMPREPLY[*]}" ]]
}

@test "nd toolbelt does not autocomplete aliases" {
    _setup_test_directory

    alias nd-some-test-command="echo test"

    COMP_WORDS=("nd" "some-test-com")
    COMP_CWORD=1

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

    COMP_WORDS=("nd" "some-test-com")
    COMP_CWORD=1

    eval "$(nd init -)"
    _ndtoolbelt_autocomplete_hook
    [ -z "$COMPREPLY" ]

    # Verifies this test is setup correctly.
    touch $TEST_DIRECTORY/nd-some-test-command
    chmod +x $TEST_DIRECTORY/nd-some-test-command

    _ndtoolbelt_autocomplete_hook
    [ -n "$COMPREPLY" ]
}

@test "nd creates the '.updated' file if it does not exist" {
    export ND_TOOLBELT_ROOT=$BATS_TEST_DIRNAME/..
    updated_path=$ND_TOOLBELT_ROOT/.updated
    rm -f $updated_path
    nd version

    [[ -f $updated_path ]]
}

@test "nd updates the '.updated' file timestamp no more than once an hour" {
    export ND_TOOLBELT_ROOT=$BATS_TEST_DIRNAME/..
    updated_path=$ND_TOOLBELT_ROOT/.updated
    rm -f $updated_path

    touch -d "55 minutes ago" $updated_path
    last_timestamp=$(stat -c %Y $updated_path)
    nd version
    [[ "$(stat -c %Y $updated_path)" = $last_timestamp ]]

    touch -d "60 minutes ago" $updated_path
    last_timestamp=$(stat -c %Y $updated_path)
    nd version
    [[ "$(stat -c %Y $updated_path)" != $last_timestamp ]]
}

@test "nd automatically updates itself from the remote repo" {
    _setup_test_directory
    branch=$(git rev-parse --abbrev-ref HEAD)

    # Create a "remote" repo with a new version of nd
    git clone . $TEST_DIRECTORY/nd-toolbelt-remote
    pushd $TEST_DIRECTORY/nd-toolbelt-remote
    echo "#!/usr/bin/env bash" > bin/nd
    echo "echo my-updated-nd \$*" >> bin/nd
    git add bin/nd
    git commit -m 'Test'
    popd

    # Create a clone of the original repo without the change but with the "remote" as the origin
    export ND_TOOLBELT_ROOT=$TEST_DIRECTORY/nd-toolbelt
    git clone . $TEST_DIRECTORY/nd-toolbelt

    # Run nd in the clone
    cd $TEST_DIRECTORY/nd-toolbelt
    git remote rm origin
    git remote add origin $TEST_DIRECTORY/nd-toolbelt-remote

    virtualenv .venv
    source .venv/bin/activate
    pip install -e .
    actual=$(nd --some-new-flag-that-does-not-exist-yet version)
    [[ $actual = "my-updated-nd --some-new-flag-that-does-not-exist-yet version" ]]
}

@test "'nd help' runs nd-help --help" {
    actual=$(nd help)
    expected=$(nd-help --help)
    [[ "$actual" = "$expected" && -n "$actual" ]]
}

@test "'nd help <command>' runs '<command> --help'" {
    actual=$(nd help init)
    expected=$(nd-init --help)
    [[ "$actual" = "$expected" && -n "$actual" ]]
}
