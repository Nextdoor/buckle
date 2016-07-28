#!/usr/bin/env bats

load test_helpers

setup() {
	_shared_setup
	eval "$(nd init -)"
}

make_empty_command() {
	make_executable_command "${@}" < /dev/null
}

@test "'nd <tab>' autocompletes commands that begin with 'nd-'" {
	make_empty_command nd-my-command
	COMP_WORDS=(nd my)
	COMP_CWORD=1 _ndtoolbelt_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[*]}" ]]
}

@test "'nd <tab>' autocompletes commands that appear twice on the path" {
	make_empty_command nd-my-command TEST_DIR
	make_empty_command nd-my-command TEST_DIR2
	# Make sure it appears twice
	found=($(compgen -c nd-my-command))
	[[ "${found[@]}" = "nd-my-command nd-my-command" ]]

	COMP_WORDS=(nd my-c)
	COMP_CWORD=1 _ndtoolbelt_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[*]}" ]]
}

@test "'nd <namespace> <tab>' completes commands that begin with 'nd~<namespace>'" {
	make_empty_command nd-my-namespace~my-command

	COMP_WORDS=("nd" "my-namespace" "my")
	COMP_CWORD=2 _ndtoolbelt_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[*]}" ]]
}

@test "'nd <namespace> <subnamespace> <tab>' completes commands" {
	make_empty_command nd-my-namespace~my-subnamespace~my-command

	COMP_WORDS=( nd my-namespace my-subnamespace my)
	COMP_CWORD=3 _ndtoolbelt_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[*]}" ]]
}

@test "'nd <namespace> <tab>' does not complete grandchildren namespaces" {
	make_empty_command nd-grandparent-namespace~parent-namespace~child_my-command

	COMP_WORDS=(nd grandparent-namespace)
	COMP_CWORD=2 _ndtoolbelt_autocomplete_hook
	[[ "parent-namespace help" = "${COMPREPLY[*]}" ]]
}

@test "nd toolbelt does not autocomplete aliases" {
	make_empty_command nd-my-command TEST_DIR
	COMP_WORDS=(nd my-com)
	COMP_CWORD=1
	_ndtoolbelt_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[*]}" ]]

	# Try an alias instead
	alias nd-my-command="echo test"
	rm $TEST_DIR/nd-my-command
	_ndtoolbelt_autocomplete_hook
	[ -z "$COMPREPLY" ]
}

@test "nd toolbelt does not autocomplete functions" {
	make_empty_command nd-my-command TEST_DIR
	COMP_WORDS=(nd my-com)
	COMP_CWORD=1
	_ndtoolbelt_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[*]}" ]]

	# Try a function instead
	nd-my-commmand() { true; }
	rm $TEST_DIR/nd-my-command
	_ndtoolbelt_autocomplete_hook
	[ -z "$COMPREPLY" ]
}

@test "'nd help' autocomplete returns matches that begin with nd" {
	make_empty_command nd-toolbelt-my-command
	COMP_WORDS=(nd help toolbelt-my)
	COMP_CWORD=2 _ndtoolbelt_autocomplete_hook
	[[ "toolbelt-my-command" = "${COMPREPLY[*]}" ]]
}

@test "'nd <namespace> help' autocomplete returns matches that begin with nd <namespace>" {
	make_empty_command nd-my-namespace~my-command
	chmod +x $TEST_DIRECTORY/nd-my-namespace~my-command

	COMP_WORDS=(nd my-namespace help my)
	COMP_CWORD=3 _ndtoolbelt_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[*]}" ]]
}

@test "'nd <namespace> <subnamespace> help <tab>' shows subnamespace commands" {
	make_empty_command nd-grandparent-namespace~parent-namespace~child-namespace~my-command

	COMP_WORDS=(nd grandparent-namespace parent-namespace help child)
	COMP_CWORD=4 _ndtoolbelt_autocomplete_hook
	[[ "child-namespace" = "${COMPREPLY[*]}" ]]
}

@test "'nd help <tab>' shows all namespaces" {
	make_empty_command nd-my-namespace~my-command

	COMP_WORDS=(nd help my-na)
	COMP_CWORD=2 _ndtoolbelt_autocomplete_hook
	[[ "my-namespace" = "${COMPREPLY[*]}" ]]
}

@test "'nd help help <tab>' does not include 'help' again in the autocomplete choices" {
	COMP_WORDS=(nd help help)
	COMP_CWORD=3 _ndtoolbelt_autocomplete_hook
	[[ -z "${COMPREPLY[*]}" ]]
}

@test "'nd <namespace> <tab>' includes 'help' in the options" {
	make_empty_command nd-my-namespace~my-command

	COMP_WORDS=(nd my-namespace)
	COMP_CWORD=2 _ndtoolbelt_autocomplete_hook
	[[ "my-command help" = "${COMPREPLY[*]}" ]]
}

@test "'nd <namespace> h<tab>' includes 'help' in the options" {
	make_empty_command nd-my-namespace~my-command

	COMP_WORDS=(nd my-namespace h)
	COMP_CWORD=2 _ndtoolbelt_autocomplete_hook
	[[ "help" = "${COMPREPLY[*]}" ]]
}

@test "'nd <namespace> help <tab>' does not include 'help' in the options" {
	make_empty_command nd-my-namespace~my-command

	COMP_WORDS=(nd my-namespace help)
	COMP_CWORD=3 _ndtoolbelt_autocomplete_hook
	[[ "my-command" = "${COMPREPLY[*]}" ]]
}

@test "'nd <namespace> <command> <tab>' does not include 'help' in the options" {
	make_empty_command nd-my-namespace~my-command

	COMP_WORDS=(nd my-namespace my-command)
	COMP_CWORD=3 _ndtoolbelt_autocomplete_hook
	[[ "" = "${COMPREPLY[*]}" ]]
}

@test "'nd <tab>' does not include '_'* in the options until the user presses '_'" {
	make_empty_command nd-_my-command

	COMP_WORDS=(nd)
	COMP_CWORD=1 _ndtoolbelt_autocomplete_hook
	[[  "${COMPREPLY[*]}" != *"_my-command"* ]]

	COMP_WORDS=(nd '_')
	COMP_CWORD=1 _ndtoolbelt_autocomplete_hook
	[[ "${COMPREPLY[*]}" = *"_my-command"* ]]
}

@test "'nd <tab>' does not include '.'* in the options until the user presses '.'" {
	make_empty_command nd-.my-command

	COMP_WORDS=(nd)
	COMP_CWORD=1 _ndtoolbelt_autocomplete_hook
	[[  "${COMPREPLY[*]}" != *".my-command"* ]]

	COMP_WORDS=(nd '.')
	COMP_CWORD=1 _ndtoolbelt_autocomplete_hook
	[[ "${COMPREPLY[*]}" = *".my-command"* ]]
}

@test "'nd -<option> <namespace> <tab>' still returns commands in the given namespace" {
	make_empty_command nd-my-namespace~my-command

	COMP_WORDS=(nd -some-option my-namespace)
	COMP_CWORD=3 _ndtoolbelt_autocomplete_hook
	[[  "${COMPREPLY[*]}" = "my-command help" ]]

	COMP_WORDS=(nd --some-option my-namespace)
	COMP_CWORD=3 _ndtoolbelt_autocomplete_hook
	[[  "${COMPREPLY[*]}" = "my-command help" ]]
}

@test "'nd -<option>=<arg> <namespace> <tab>' still returns commands in the given namespace" {
	make_empty_command nd-my-namespace~my-command

	COMP_WORDS=(nd -some-option=10 my-namespace)
	COMP_CWORD=3 _ndtoolbelt_autocomplete_hook
	[[  "${COMPREPLY[*]}" = "my-command help" ]]

	COMP_WORDS=(nd --some-option=10 my-namespace)
	COMP_CWORD=3 _ndtoolbelt_autocomplete_hook
	[[  "${COMPREPLY[*]}" = "my-command help" ]]
}

@test "'nd <namespace> -<option> <tab>' autocomplete does not return namespace completions" {
	make_empty_command nd-my-namespace~my-command

	COMP_WORDS=(nd my-namespace -some-option my-co)
	COMP_CWORD=3 _ndtoolbelt_autocomplete_hook
	[[  -z "${COMPREPLY[*]}" ]]

	COMP_WORDS=(nd my-namespace --some-option my-co)
	COMP_CWORD=3 _ndtoolbelt_autocomplete_hook
	[[  -z "${COMPREPLY[*]}" ]]
}
