#!/usr/bin/env bats

setup() {
    _setup_tmp_directory

    # Create a fake git root so update checks happen quickly
    fake_root=$TMPDIR/fake-root
    mkdir $fake_root
    touch $fake_root/.updated
    export ND_TOOLBELT_ROOT=$fake_root

    # Pretend the clock was checked recently so we don't repeat the check on each test
    touch $TMPDIR/.nd_toolbelt_clock_last_checked
}

_setup_tmp_directory() {
    export TMPDIR="$(mktemp -d nd-toolbelt_test_tmp.XXXXX --tmpdir)"
    _append_to_exit_trap "rm -rf $TMPDIR"
}

_setup_test_directory() {
    TEST_DIRECTORY="$(mktemp -d nd-toolbelt_test.XXXXX --tmpdir)"
    _append_to_exit_trap "rm -rf $TEST_DIRECTORY"
    PATH=$TEST_DIRECTORY:$PATH
}

_append_to_exit_trap() {
    # Makes sure to run the existing exit handler
    trap "$1; $(trap -p EXIT | sed -r "s/trap.*?'(.*)' \w+$/\1/")" EXIT
}

@test "'nd version' matches 'nd-version'" {
    actual="$(nd version)"
    expected="$(nd-version)"
    [[ "$actual" = "$expected" && -n "$actual" ]]
}

@test "'nd init -' returns 0 exit code" {
    actual="$(nd init -)"
    expected="$(cat nd_toolbelt/nd-init.sh)"  # TODO(hramos): Make not relative path?
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

@test "'nd <namespace> <command>' runs 'nd-<namespace>~<command>'" {
    _setup_test_directory
    echo "#!/usr/bin/env bash" > $TEST_DIRECTORY/nd-namespace-test~command-test
    echo "echo \$*" >> $TEST_DIRECTORY/nd-namespace-test~command-test
    chmod +x $TEST_DIRECTORY/nd-namespace-test~command-test

    result="$(nd namespace-test command-test -a -b -c --f test)"
    [[ "$result" = "-a -b -c --f test" ]]
}

@test "nd toolbelt rejects options not handled" {
    nd -random-test-option version && failed=1
    [[ -z "$failed" ]]
}

@test "Options from \$ND_TOOLBELT_OPTS are used by nd" {
    export ND_TOOLBELT_ROOT=$BATS_TEST_DIRNAME/..
    updated_path=$ND_TOOLBELT_ROOT/.updated

    export ND_TOOLBELT_OPTS='--update-freq "300" --update'
    touch -d "5 minutes ago" $updated_path
    last_timestamp=$(stat -c %Y $updated_path)
    nd version
    [[ "$(stat -c %Y $updated_path)" != $last_timestamp ]]
}

@test "'nd <tab>' autocompletes commands that begin with 'nd-'" {
    _setup_test_directory

    touch $TEST_DIRECTORY/nd-toolbelt-my-command
    chmod +x $TEST_DIRECTORY/nd-toolbelt-my-command

    COMP_WORDS=("nd" "toolbelt-my")
    COMP_CWORD=1

    eval "$(nd init -)"
    _ndtoolbelt_autocomplete_hook
    [[ "toolbelt-my-command" = "${COMPREPLY[*]}" ]]
}

@test "'nd <tab>' autocompletes commands that appear twice on the path" {
    _setup_test_directory

    touch $TEST_DIRECTORY/nd-my-command
    chmod +x $TEST_DIRECTORY/nd-my-command

    mkdir $TEST_DIRECTORY/second_test_directory
    cp $TEST_DIRECTORY/nd-my-command $TEST_DIRECTORY/second_test_directory/nd-my-command

    PATH=$TEST_DIRECTORY/second_test_directory:$PATH

    COMP_WORDS=("nd" "my-c")
    COMP_CWORD=1

    eval "$(nd init -)"
    _ndtoolbelt_autocomplete_hook
    [[ "my-command" = "${COMPREPLY[*]}" ]]
}

@test "'nd <namespace> <tab>' completes commands that begin with 'nd~<namespace>'" {
    _setup_test_directory

    touch $TEST_DIRECTORY/nd-my-namespace~my-command
    chmod +x $TEST_DIRECTORY/nd-my-namespace~my-command

    COMP_WORDS=("nd" "my-namespace" "my")
    COMP_CWORD=2

    eval "$(nd init -)"
    _ndtoolbelt_autocomplete_hook
    [[ "my-command" = "${COMPREPLY[*]}" ]]
}

@test "'nd <namespace> <subnamespace> <tab>' completes commands" {
    _setup_test_directory

    touch $TEST_DIRECTORY/nd-my-namespace~my-subnamespace~my-command
    chmod +x $TEST_DIRECTORY/nd-my-namespace~my-subnamespace~my-command

    COMP_WORDS=("nd" "my-namespace" "my-subnamespace" "my")
    COMP_CWORD=3

    eval "$(nd init -)"
    _ndtoolbelt_autocomplete_hook
    [[ "my-command" = "${COMPREPLY[*]}" ]]
}

@test "'nd <namespace> <tab>' does not complete grandchildren namespaces" {
    _setup_test_directory

    touch $TEST_DIRECTORY/nd-grandparent-namespace~parent-namespace~child_my-command
    chmod +x $TEST_DIRECTORY/nd-grandparent-namespace~parent-namespace~child_my-command

    COMP_WORDS=("nd" "grandparent-namespace")
    COMP_CWORD=2

    eval "$(nd init -)"
    _ndtoolbelt_autocomplete_hook
    [[ "parent-namespace" = "${COMPREPLY[*]}" ]]
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

@test "'nd help' autocomplete returns matches that begin with nd" {
    _setup_test_directory

    touch $TEST_DIRECTORY/nd-toolbelt-my-command
    chmod +x $TEST_DIRECTORY/nd-toolbelt-my-command

    COMP_WORDS=("nd" "help" "toolbelt-my")
    COMP_CWORD=2

    eval "$(nd init -)"
    _ndtoolbelt_autocomplete_hook
    [[ "toolbelt-my-command" = "${COMPREPLY[*]}" ]]
}

@test "'nd <namespace> help' autocomplete returns matches that begin with nd <namespace>" {
    _setup_test_directory

    touch $TEST_DIRECTORY/nd-my-namespace~my-command
    chmod +x $TEST_DIRECTORY/nd-my-namespace~my-command

    COMP_WORDS=("nd" "my-namespace" "help" "my")
    COMP_CWORD=3

    eval "$(nd init -)"
    _ndtoolbelt_autocomplete_hook
    [[ "my-command" = "${COMPREPLY[*]}" ]]
}

@test "'nd help --exclude <filename>' excludes filename from help prompt" {
    _setup_test_directory

    cp tests/fixtures/sample-help-command.py $TEST_DIRECTORY/nd-my-excluded-command
    chmod +x $TEST_DIRECTORY/nd-my-excluded-command

    result=$(nd help --exclude nd-my-excluded-command)
    [[ "$result" != *"my-excluded-command"* ]]
}

@test "'nd help <filename>' does not run --help on the file if filename is excluded in nd-help" {
    _setup_test_directory

    cp tests/fixtures/sample-help-command.py $TEST_DIRECTORY/nd-my-excluded-command
    chmod +x $TEST_DIRECTORY/nd-my-excluded-command

    result=$( { nd help --exclude nd-my-excluded-command my-excluded-command; } 2>&1 )
    [[ "$result" == *"ERROR: nd: executable nd-my-excluded-command excluded from nd help"* ]]
}

@test "'nd <namespace> <subnamespace> help' autocomplete returns matches" {
    _setup_test_directory

    touch $TEST_DIRECTORY/nd-grandparent-namespace~parent-namespace~child-namespace~my-command
    chmod +x $TEST_DIRECTORY/nd-grandparent-namespace~parent-namespace~child-namespace~my-command

    COMP_WORDS=("nd" "grandparent-namespace" "parent-namespace" "help" "child")
    COMP_CWORD=4

    eval "$(nd init -)"
    _ndtoolbelt_autocomplete_hook
    [[ "child-namespace" = "${COMPREPLY[*]}" ]]
}

@test "'nd help' autocomplete returns namespaces" {
    _setup_test_directory

    touch $TEST_DIRECTORY/nd-my-namespace~my-command
    chmod +x $TEST_DIRECTORY/nd-my-namespace~my-command

    COMP_WORDS=("nd" "help" "my-na")
    COMP_CWORD=2

    eval "$(nd init -)"
    _ndtoolbelt_autocomplete_hook
    [[ "my-namespace" = "${COMPREPLY[*]}" ]]
}

@test "'nd help' returns help of all nd commands" {
    _setup_test_directory

    cp tests/fixtures/sample-help-command.py $TEST_DIRECTORY/nd-my-command
    chmod +x $TEST_DIRECTORY/nd-my-command

    result=$(nd help)
    [[ $result == *"Help for command nd-my-command"* ]]
}

@test "'nd help' returns help of nd namespaced commands" {
    _setup_test_directory

    cp tests/fixtures/sample-help-command.py $TEST_DIRECTORY/nd-my-command
    chmod +x $TEST_DIRECTORY/nd-my-command

    cp tests/fixtures/sample-help-command.py $TEST_DIRECTORY/nd-my-namespace~my-command
    chmod +x $TEST_DIRECTORY/nd-my-namespace~my-command

    result=$(nd help)
    [[ $result == *"Help for command nd-my-command"* ]]
    [[ $result == *"Help for command nd-my-namespace"* ]]
}

@test "'nd help <namespace>' returns help for commands in the namespace" {
    _setup_test_directory

    cp tests/fixtures/sample-help-command.py $TEST_DIRECTORY/nd-my-namespace~my-command
    chmod +x $TEST_DIRECTORY/nd-my-namespace~my-command

    result=$(nd help my-namespace)
    [[ $result == *"Help for command nd-my-namespace"* ]]
}

@test "'nd help <command>' runs '<command> --help'" {
    actual=$(nd help init)
    expected=$(nd-init --help)
    [[ "$actual" = "$expected" && -n "$actual" ]]
}

@test "'nd help' returns '<help not found>' if a command's help returns non-zero exit status" {
    _setup_test_directory

    echo "#!/usr/bin/env bash" > $TEST_DIRECTORY/nd-command-test
    echo "exit 1" >> $TEST_DIRECTORY/nd-command-test
    chmod +x $TEST_DIRECTORY/nd-command-test

    result=$(nd help)
    echo "$result" | grep -E "command-test\s+<help not found>"
}

@test "'nd help' returns '<help not found>' if a command's help can't be parsed" {
    _setup_test_directory

    touch $TEST_DIRECTORY/nd-command-test
    chmod +x $TEST_DIRECTORY/nd-command-test

    result=$(nd help)
    echo "$result" | grep -E "command-test\s+<help not found>"
}

@test "nd creates the '.updated' file if it does not exist" {
    export ND_TOOLBELT_ROOT=$BATS_TEST_DIRNAME/..
    updated_path=$ND_TOOLBELT_ROOT/.updated
    rm -f $updated_path
    nd version

    [[ -f $updated_path ]]
}

@test "nd toolbelt updates the '.updated' file timestamp no more than once an hour" {
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

@test "'nd --update <command>' always tries to update itself from the remote repo" {
    export ND_TOOLBELT_ROOT=$BATS_TEST_DIRNAME/..
    updated_path=$ND_TOOLBELT_ROOT/.updated
    cd /  # Ensure that cwd location does not affect update process

    touch -d "55 minutes ago" $updated_path
    last_timestamp=$(stat -c %Y $updated_path)
    nd --update version
    [[ "$(stat -c %Y $updated_path)" != $last_timestamp ]]
}

@test "'nd --no-update <command>' does not update itself from the remote repo" {
    export ND_TOOLBELT_ROOT=$BATS_TEST_DIRNAME/..
    updated_path=$ND_TOOLBELT_ROOT/.updated

    touch -d "60 minutes ago" $updated_path
    last_timestamp=$(stat -c %Y $updated_path)
    nd --no-update version
    [[ "$(stat -c %Y $updated_path)" = $last_timestamp ]]
}

@test "'nd --update-freq <seconds> <command>' updates with the given frequency" {
    export ND_TOOLBELT_ROOT=$BATS_TEST_DIRNAME/..
    updated_path=$ND_TOOLBELT_ROOT/.updated

    touch -d "5 minutes ago" $updated_path
    last_timestamp=$(stat -c %Y $updated_path)
    nd --update-freq 300 version
    [[ "$(stat -c %Y $updated_path)" != $last_timestamp ]]
}

@test "nd toolbelt warns the user if the machine time offset by at least 120 seconds" {
    clock_checked_path=$TMPDIR/.nd_toolbelt_clock_last_checked
    rm -f $clock_checked_path

    eval "$(python-libfaketime)"
    stderr=$(FAKETIME=-120 nd version 2>&1 >/dev/null)
    [[ $stderr == *"The system clock is behind by"* ]]
}

@test "nd toolbelt deletes the .nd_toolbelt_clock_last_checked file if clock is out of date" {
    clock_checked_path=$TMPDIR/.nd_toolbelt_clock_last_checked
    rm -f $clock_checked_path

    eval "$(python-libfaketime)"
    FAKETIME=-120 nd version 2>&1 >/dev/null
    [ ! -f $clock_checked_path ]
}

@test "nd toolbelt checks the system time no more than once every 10 minutes" {
    clock_checked_path=$TMPDIR/.nd_toolbelt_clock_last_checked
    rm -f $clock_checked_path

    touch -d "7 minutes ago" $clock_checked_path
    last_timestamp=$(stat -c %Y $clock_checked_path)
    nd version
    [[ "$(stat -c %Y $clock_checked_path)" = $last_timestamp ]]

    touch -d "10 minutes ago" $clock_checked_path
    last_timestamp=$(stat -c %Y $clock_checked_path)
    nd version
    [[ "$(stat -c %Y $clock_checked_path)" != $last_timestamp ]]
}

@test "nd toolbelt automatically updates itself from the remote repo" {
    _setup_test_directory
    branch=$(git rev-parse --abbrev-ref HEAD)
    unset ND_TOOLBELT_ROOT

    # Create a "remote" repo with a new version of nd
    git clone . $TEST_DIRECTORY/nd-toolbelt-remote
    pushd $TEST_DIRECTORY/nd-toolbelt-remote
    echo "#!/usr/bin/env bash" > bin/nd
    echo "echo my-updated-nd \$*" >> bin/nd
    git config user.email "test@example.com"
    git config user.name "test"
    git add bin/nd
    git commit -m 'Test'
    popd

    # Create a clone of the original repo without the change but with the "remote" as the origin
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
