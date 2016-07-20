#!/usr/bin/env bats

load test_helpers

setup() {
    _shared_setup
    _setup_test_directory TEST_DIR
}

@test "'nd help' returns help of all nd commands" {
    cp $BATS_TEST_DIRNAME/fixtures/sample-help-command.py $TEST_DIR/nd-my-command

    result=$(nd help)
    [[ $result == *"Help for command nd-my-command"* ]]
}

@test "'nd help' returns help of nd namespaced commands" {
    cp $BATS_TEST_DIRNAME/fixtures/sample-help-command.py $TEST_DIR/nd-my-command
    cp $BATS_TEST_DIRNAME/fixtures/sample-help-command.py $TEST_DIR/nd-my-namespace~my-command

    result=$(nd help)
    [[ $result == *"Help for command nd-my-command"* ]]
    [[ $result == *"Help for command nd-my-namespace~my-command"* ]]
}

@test "'nd help <namespace>' returns help for commands in the namespace" {
    cp $BATS_TEST_DIRNAME/fixtures/sample-help-command.py $TEST_DIR/nd-my-namespace~my-command

    result=$(nd help my-namespace)
    [[ $result == *"Help for command nd-my-namespace~my-command"* ]]
}

@test "'nd <namespace> help' returns help for the commands in the namespace" {
    cp $BATS_TEST_DIRNAME/fixtures/sample-help-command.py $TEST_DIR/nd-my-namespace~my-command

    result=$(nd my-namespace help)
    [[ $result == *"Help for command nd-my-namespace~my-command"* ]]
}

@test "'nd <namespace> help <command>' returns help for the commands in the namespace" {
    cp $BATS_TEST_DIRNAME/fixtures/sample-help-command.py $TEST_DIR/nd-my-namespace~my-command

    result=$(nd my-namespace help my-command)
    [[ $result == *"Help for command nd-my-namespace~my-command"* ]]
}

@test "'nd <namespace> help <subnamespace>' returns help for the commands in the namespace" {
    cp $BATS_TEST_DIRNAME/fixtures/sample-help-command.py \
    	$TEST_DIR/nd-my-namespace~subnamespace~my-command

    result=$(nd my-namespace help subnamespace)
    [[ "$result" == *"my-namespace subnamespace my-command"* ]]
    [[ "$result" == *"Help for command"* ]]
}

@test "'nd help <command>' runs '<command> --help'" {
    actual=$(nd help init)
    expected=$(nd-init --help)
    [[ "$actual" = "$expected" && -n "$actual" ]]
}

@test "'nd help' returns '<help not found>' if a command's help returns non-zero exit status" {
	make_executable_command nd-command-test <<- 'EOF'
		#!/usr/bin/env bash
		exit 1
EOF

    result=$(nd help)
    echo "$result" | grep -E "command-test\s+<help not found>"
}

@test "'nd help' returns '<help not found>' if a command's help can't be parsed" {
	make_executable_command nd-command-test < /dev/null

    result=$(nd help)
    echo "$result" | grep -E "command-test\s+<help not found>"
}
