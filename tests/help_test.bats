#!/usr/bin/env bats

load test_helpers

setup() {
	_shared_setup belt
	_setup_test_directory TEST_DIR
}

@test "'belt help' returns help of all commands with prefix" {
	cp $BATS_TEST_DIRNAME/fixtures/sample-help-command.py $TEST_DIR/belt-my-command

	result=$(belt help)
	[[ $result == *"Help for command belt-my-command"* ]]
}

@test "'belt help' returns help of nd namespaced commands" {
	cp $BATS_TEST_DIRNAME/fixtures/sample-help-command.py $TEST_DIR/belt-my-command
	cp $BATS_TEST_DIRNAME/fixtures/sample-help-command.py $TEST_DIR/belt-my-namespace~my-command

	result=$(belt help)
	[[ $result == *"Help for command belt-my-command"* ]]
	[[ $result == *"Help for command belt-my-namespace~my-command"* ]]
}

@test "'belt help <namespace>' returns help for commands in the namespace" {
	cp $BATS_TEST_DIRNAME/fixtures/sample-help-command.py $TEST_DIR/belt-my-namespace~my-command

	result=$(belt help my-namespace)
	[[ $result == *"Help for command belt-my-namespace~my-command"* ]]
}

@test "'belt <namespace> help' returns help for the commands in the namespace" {
	cp $BATS_TEST_DIRNAME/fixtures/sample-help-command.py $TEST_DIR/belt-my-namespace~my-command

	result=$(belt my-namespace help)
	[[ $result == *"Help for command belt-my-namespace~my-command"* ]]
}

@test "'belt <namespace> help <command>' returns help for the commands in the namespace" {
	cp $BATS_TEST_DIRNAME/fixtures/sample-help-command.py $TEST_DIR/belt-my-namespace~my-command

	result=$(belt my-namespace help my-command)
	[[ $result == *"Help for command belt-my-namespace~my-command"* ]]
}

@test "'belt <namespace> help <subnamespace>' returns help for the commands in the namespace" {
	cp $BATS_TEST_DIRNAME/fixtures/sample-help-command.py \
		$TEST_DIR/belt-my-namespace~subnamespace~my-command

	result=$(belt my-namespace help subnamespace)
	[[ "$result" == *"my-namespace subnamespace my-command"* ]]
	[[ "$result" == *"Help for command"* ]]
}

@test "'belt help <command>' runs '<command> --help'" {
	make_executable_command belt-command-test <<- 'EOF'
		#!/usr/bin/env bash
		echo "Got $1"
EOF

	result=$(belt help)
	echo "$result" | grep -E "command-test\s+Got --help"
}

@test "'belt help' returns '<help not found>' if a command's help returns non-zero exit status" {
	make_executable_command belt-command-test <<- 'EOF'
		#!/usr/bin/env bash
		exit 1
EOF

	result=$(belt help)
	echo "$result" | grep -E "command-test\s+<help not found>"
}

@test "'belt help' returns '<help not found>' if a command's help can't be parsed" {
	make_executable_command belt-command-test <<- 'EOF'
		#!/usr/bin/env bash
		exit 0
EOF

	result=$(belt help)
	echo "$result" | grep -E "command-test\s+<help not found>"
}
