_setup_alias() {
    local command=$1
	alias $command="BUCKLE_TOOLBELT_NAME=$1 buckle"
	shopt -s expand_aliases
}

_setup_tmp_directory() {
    export TMPDIR="$(mktemp -d buckle_test_tmp.XXXXX --tmpdir)"
    _append_to_exit_trap "rm -rf $TMPDIR"
}

_setup_test_directory() {
    # Create a directory and add it to the PATH
    # Store the path in the variable name provided in $1 (defaults to TEST_DIRECTORY)
    local var_name=${1:-TEST_DIRECTORY}
    local test_dir="$(mktemp -d buckle_test.XXXXX --tmpdir)"
    _append_to_exit_trap "rm -rf $test_dir"
    PATH="$test_dir:$PATH"
    declare -g "$var_name"="$test_dir"
}

_append_to_exit_trap() {
    # Makes sure to run the existing exit handler
    trap "$1; $(trap -p EXIT | sed -r "s/trap.*?'(.*)' \w+$/\1/")" EXIT
}

_shared_setup() {
    local command=$1
    _setup_tmp_directory
    # Create a fake git root so update checks happen quickly
    fake_root=$TMPDIR/fake-root
    mkdir $fake_root
    touch $fake_root/.updated
    export BUCKLE_ROOT=$fake_root

    # Pretend the clock was checked recently so we don't repeat the check on each test
    touch $TMPDIR/.buckle_clock_last_checked

    _setup_alias $command
}

make_executable_command() {
	# Creates a command in a new directory in path with contents from standard input
	# Args:
	#  - Name of command
	#  - (optional) Name of variable to store the name of newly created directory with the command
	local name="$1"
	local dirref="${2:-TEST_DIRECTORY}"
    local command
    readarray command

    _setup_test_directory "$dirref"
    local file="${!dirref}/$name"

    printf '%s\n' "${command[@]}" > "$file"
    chmod +x "$file"
}
