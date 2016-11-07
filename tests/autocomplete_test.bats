#!/usr/bin/env bats

load test_helpers

setup() {
	_shared_setup ns
	source $BATS_TEST_DIRNAME/../buckle/init.sh -
	_buckle_autocomplete_setup belt
}

make_empty_command() {
	make_executable_command "${@}" < /dev/null
}

@test "'belt <tab>' autocompletes commands that begin with 'belt-'" {
	make_empty_command belt-my-command
	COMP_WORDS=(belt my)
	COMP_CWORD=1 _buckle_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[*]}" ]]
}

@test "'belt <tab>' autocompletes commands that appear twice on the path" {
	make_empty_command belt-my-command TEST_DIR
	make_empty_command belt-my-command TEST_DIR2
	# Make sure it appears twice
	found=($(compgen -c belt-my-command))
	[[ "${found[@]}" = "belt-my-command belt-my-command" ]]

	COMP_WORDS=(belt my-c)
	COMP_CWORD=1 _buckle_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[*]}" ]]
}

@test "'belt <namespace> <tab>' completes commands that begin with 'belt~<namespace>'" {
	make_empty_command belt-my-namespace~my-command

	COMP_WORDS=("belt" "my-namespace" "my")
	COMP_CWORD=2 _buckle_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[*]}" ]]
}

@test "'belt <namespace> <subnamespace> <tab>' completes commands" {
	make_empty_command belt-my-namespace~my-subnamespace~my-command

	COMP_WORDS=( belt my-namespace my-subnamespace my)
	COMP_CWORD=3 _buckle_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[*]}" ]]
}

@test "'belt <namespace> <tab>' does not complete grandchildren namespaces" {
	make_empty_command belt-grandparent-namespace~parent-namespace~child_my-command

	COMP_WORDS=(belt grandparent-namespace)
	COMP_CWORD=2 _buckle_autocomplete_hook
	[[ "parent-namespace help" = "${COMPREPLY[*]}" ]]
}

@test "buckle does not autocomplete aliases" {
	make_empty_command belt-my-command TEST_DIR
	COMP_WORDS=(belt my-com)
	COMP_CWORD=1
	_buckle_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[*]}" ]]

	# Try an alias instead
	alias belt-my-command="echo test"
	rm $TEST_DIR/belt-my-command
	_buckle_autocomplete_hook
	[ -z "$COMPREPLY" ]
}

@test "buckle does not autocomplete functions" {
	make_empty_command belt-my-command TEST_DIR
	COMP_WORDS=(belt my-com)
	COMP_CWORD=1
	_buckle_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[*]}" ]]

	# Try a function instead
	belt-my-commmand() { true; }
	rm $TEST_DIR/belt-my-command
	_buckle_autocomplete_hook
	[ -z "$COMPREPLY" ]
}

@test "'belt help' autocomplete returns matches that begin with belt" {
	make_empty_command belt-toolbelt-my-command
	COMP_WORDS=(belt help toolbelt-my)
	COMP_CWORD=2 _buckle_autocomplete_hook
	[[ "toolbelt-my-command" = "${COMPREPLY[*]}" ]]
}

@test "'belt <namespace> help' autocomplete returns matches that begin with belt <namespace>" {
	make_empty_command belt-my-namespace~my-command
	chmod +x $TEST_DIRECTORY/belt-my-namespace~my-command

	COMP_WORDS=(belt my-namespace help my)
	COMP_CWORD=3 _buckle_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[*]}" ]]
}

@test "'belt <namespace> <subnamespace> help <tab>' shows subnamespace commands" {
	make_empty_command belt-grandparent-namespace~parent-namespace~child-namespace~my-command

	COMP_WORDS=(belt grandparent-namespace parent-namespace help child)
	COMP_CWORD=4 _buckle_autocomplete_hook
	[[ "child-namespace" = "${COMPREPLY[*]}" ]]
}

@test "'belt help <tab>' shows all namespaces" {
	make_empty_command belt-my-namespace~my-command

	COMP_WORDS=(belt help my-na)
	COMP_CWORD=2 _buckle_autocomplete_hook
	[[ "my-namespace" = "${COMPREPLY[*]}" ]]
}

@test "'belt help help <tab>' does not include 'help' again in the autocomplete choices" {
	COMP_WORDS=(belt help help)
	COMP_CWORD=3 _buckle_autocomplete_hook
	[[ -z "${COMPREPLY[*]}" ]]
}

@test "'belt <namespace> <tab>' includes 'help' in the options" {
	make_empty_command belt-my-namespace~my-command

	COMP_WORDS=(belt my-namespace)
	COMP_CWORD=2 _buckle_autocomplete_hook
	[[ "my-command help" = "${COMPREPLY[*]}" ]]
}

@test "'belt <namespace> h<tab>' includes 'help' in the options" {
	make_empty_command belt-my-namespace~my-command

	COMP_WORDS=(belt my-namespace h)
	COMP_CWORD=2 _buckle_autocomplete_hook
	[[ "help" = "${COMPREPLY[*]}" ]]
}

@test "'belt <namespace> help <tab>' does not include 'help' in the options" {
	make_empty_command belt-my-namespace~my-command

	COMP_WORDS=(belt my-namespace help)
	COMP_CWORD=3 _buckle_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[*]}" ]]
}

@test "'belt <namespace> <command> <tab>' does not include 'help' in the options" {
	make_empty_command belt-my-namespace~my-command

	COMP_WORDS=(belt my-namespace my-command)
	COMP_CWORD=3 _buckle_autocomplete_hook
	[[ "" = "${COMPREPLY[*]}" ]]
}

@test "'belt <tab>' does not include '_'* in the options until the user presses '_'" {
	make_empty_command belt-_my-command

	COMP_WORDS=(belt)
	COMP_CWORD=1 _buckle_autocomplete_hook
	[[  "${COMPREPLY[*]}" != *"_my-command"* ]]

	COMP_WORDS=(belt '_')
	COMP_CWORD=1 _buckle_autocomplete_hook
	[[ "${COMPREPLY[*]}" = *"_my-command"* ]]
}

@test "'belt <tab>' does not include '.'* in the options until the user presses '.'" {
	make_empty_command belt-.my-command

	COMP_WORDS=(belt)
	COMP_CWORD=1 _buckle_autocomplete_hook
	[[  "${COMPREPLY[*]}" != *".my-command"* ]]

	COMP_WORDS=(belt '.')
	COMP_CWORD=1 _buckle_autocomplete_hook
	[[ "${COMPREPLY[*]}" = *".my-command"* ]]
}

@test "'belt -<option> <namespace> <tab>' still returns commands in the given namespace" {
	make_empty_command belt-my-namespace~my-command

	COMP_WORDS=(belt -some-option my-namespace)
	COMP_CWORD=3 _buckle_autocomplete_hook
	[[  "${COMPREPLY[*]}" = "my-command help" ]]

	COMP_WORDS=(belt --some-option my-namespace)
	COMP_CWORD=3 _buckle_autocomplete_hook
	[[  "${COMPREPLY[*]}" = "my-command help" ]]
}

@test "'belt -<option>=<arg> <namespace> <tab>' still returns commands in the given namespace" {
	make_empty_command belt-my-namespace~my-command

	COMP_WORDS=(belt -some-option=10 my-namespace)
	COMP_CWORD=3 _buckle_autocomplete_hook
	[[  "${COMPREPLY[*]}" = "my-command help" ]]

	COMP_WORDS=(belt --some-option=10 my-namespace)
	COMP_CWORD=3 _buckle_autocomplete_hook
	[[  "${COMPREPLY[*]}" = "my-command help" ]]
}

@test "'belt <namespace> -<option> <tab>' autocomplete does not return namespace completions" {
	make_empty_command belt-my-namespace~my-command

	COMP_WORDS=(belt my-namespace -some-option my-co)
	COMP_CWORD=3 _buckle_autocomplete_hook
	[[  -z "${COMPREPLY[*]}" ]]

	COMP_WORDS=(belt my-namespace --some-option my-co)
	COMP_CWORD=3 _buckle_autocomplete_hook
	[[  -z "${COMPREPLY[*]}" ]]
}

@test "'belt <namespace> <command>' shows autocomplete choices generated from user-provided command" {
    make_empty_command belt-my-namespace~my-command
    make_executable_command belt-my-namespace~my-command.completion.script <<- 'EOF'
        #!/usr/bin/env bash
		echo "${COMP_WORDS[@]} word$COMP_CWORD"
EOF
	COMP_WORDS=(belt my-namespace my-command my-arg)
	COMP_CWORD=3 _buckle_autocomplete_hook
	[[ "belt my-namespace my-command my-arg word3" = "${COMPREPLY[@]}" ]]

	# Check that autocomplete doesn't include the completion script itself
	COMP_WORDS=(belt my-namespace my-command)
	COMP_CWORD=2 _buckle_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[@]}" ]]
}

@test "'belt <namespace> <command>' includes autocomplete choices generated from namespace autocomplete command" {
    make_executable_command belt-my-namespace.completion.script <<- 'EOF'
        #!/usr/bin/env bash
		echo "${COMP_WORDS[@]} word$COMP_CWORD"
EOF
    make_executable_command belt-my-namespace~my-command.completion.script <<- 'EOF'
        #!/usr/bin/env bash
		echo "${COMP_WORDS[@]} namespace_word$COMP_CWORD"
EOF
	COMP_WORDS=(belt my-namespace my-command my-arg)
	COMP_CWORD=3 _buckle_autocomplete_hook
	[[ "belt my-namespace my-command my-arg word3 belt my-namespace my-command my-arg namespace_word3" \
	    = "${COMPREPLY[@]}" ]]
}

@test "_buckle_autocomplete_command_arg_completions sets completion from 'sourced' script output" {
    make_empty_command belt-my-namespace~my-command
    make_executable_command belt-my-namespace~my-command.completion.sh <<- 'EOF'
		echo "${COMP_WORDS[@]} word$COMP_CWORD $SOMETHING_NOT_EXPORTED"
EOF
    SOMETHING_NOT_EXPORTED=something_not_exported
    COMP_WORDS=(belt my-namespace my-command my-arg)
    COMP_CWORD=3
	NSPATH=(my-namespace my-command)
	_buckle_autocomplete_command_arg_completions COMPLETIONS belt NSPATH[@]
	[[ "belt my-namespace my-command my-arg word3 something_not_exported" = "${COMPLETIONS[@]}" ]]
}
