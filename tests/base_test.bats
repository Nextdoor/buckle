#!/usr/bin/env bats

load test_helpers

setup() {
	_shared_setup belt
}

make_null_command() {
    make_executable_command $1 <<- 'EOF'
		#!/usr/bin/env bash
		echo done
EOF
}

_set_minimal_path() {
    export PATH="$BATS_TEST_DIRNAME/../bin:/usr/bin:/bin"
    export PYTHONPATH="$BATS_TEST_DIRNAME/../:$PYTHONPATH"
}

@test "'belt version' matches 'buckle-version'" {
    _set_minimal_path

    _setup_test_directory TEST_DIR
	actual="$(BUCKLE_TOOLBELT_NAME=belt buckle version)"
	expected="$(buckle-version)"
	[[ "$actual" = "$expected" && -n "$actual" ]]
}

@test "'belt init -' returns 0 exit code" {
    _set_minimal_path

    _setup_test_directory TEST_DIR
	BUCKLE_TOOLBELT_NAME=belt run buckle init -
    [[ $status = 0 ]]
}

@test "'belt <command>' runs 'belt-<command>'" {
	make_executable_command belt-my-command <<- 'EOF'
		#!/usr/bin/env bash
		echo "$*"
EOF

	result="$(belt my-command -a -b -c --f test)"
	[[ "$result" = "-a -b -c --f test" ]]
}

@test "'belt <namespace>' runs 'buckle-help <namespace>'" {
	make_executable_command belt-my-namespace~my-command <<- 'EOF'
		#!/usr/bin/env bash
		echo my help output
EOF
	actual="$(belt my-namespace)"
	expected="$(BUCKLE_TOOLBELT_NAME=belt buckle-help my-namespace)"
	[[ "$actual" = "$expected" && "$actual" = *"my help output"* ]]
}

@test "'belt <namespace> <command>' runs 'belt-<namespace>~<command>'" {
	make_executable_command belt-my-namespace~my-command <<- 'EOF'
		#!/usr/bin/env bash
		echo "$*"
EOF

	result="$(belt my-namespace my-command -a -b -c --f arg)"
	[[ "$result" = "-a -b -c --f arg" ]]
}

@test "buckle rejects options not handled" {
    make_null_command belt-do-nothing
	BUCKLE_TOOLBELT_NAME=belt run buckle belt -random-test-option do-nothing
	[[ $status != 0 ]]
}

@test "Options from \$BUCKLE_OPTS_BELT are used by belt" {
	export BUCKLE_ROOT=$BATS_TEST_DIRNAME/..
	updated_path=$BUCKLE_ROOT/.updated
    make_null_command belt-do-nothing

	export BUCKLE_OPTS_BELT='--update-freq "300" --update'
	touch -d "5 minutes ago" $updated_path
	last_timestamp=$(stat -c %Y $updated_path)

	BUCKLE_TOOLBELT_NAME=belt buckle do-nothing
	[[ "$(stat -c %Y $updated_path)" != $last_timestamp ]]
}


@test "belt creates the '.updated' file if it does not exist" {
	export BUCKLE_ROOT=$BATS_TEST_DIRNAME/..
	updated_path=$BUCKLE_ROOT/.updated
	rm -f $updated_path
    make_null_command belt-do-nothing
	BUCKLE_TOOLBELT_NAME=belt buckle do-nothing

	[[ -f $updated_path ]]
}

@test "buckle updates the '.updated' file timestamp no more than once an hour" {
	export BUCKLE_ROOT=$BATS_TEST_DIRNAME/..
	updated_path=$BUCKLE_ROOT/.updated
	rm -f $updated_path
    make_null_command belt-do-nothing

	touch -d "55 minutes ago" $updated_path
	last_timestamp=$(stat -c %Y $updated_path)
	BUCKLE_TOOLBELT_NAME=belt buckle do-nothing
	[[ "$(stat -c %Y $updated_path)" = $last_timestamp ]]

	touch -d "60 minutes ago" $updated_path
	last_timestamp=$(stat -c %Y $updated_path)
	BUCKLE_TOOLBELT_NAME=belt buckle do-nothing
	[[ "$(stat -c %Y $updated_path)" != $last_timestamp ]]
}

@test "'belt --update <command>' always tries to update itself from the remote repo" {
	export BUCKLE_ROOT=$BATS_TEST_DIRNAME/..
	updated_path=$BUCKLE_ROOT/.updated
	cd /  # Ensure that cwd location does not affect update process
    make_null_command belt-do-nothing

	touch -d "55 minutes ago" $updated_path
	last_timestamp=$(stat -c %Y $updated_path)
	BUCKLE_TOOLBELT_NAME=belt buckle --update do-nothing
	[[ "$(stat -c %Y $updated_path)" != $last_timestamp ]]
}

@test "'belt --no-update <command>' does not update itself from the remote repo" {
	export BUCKLE_ROOT=$BATS_TEST_DIRNAME/..
	updated_path=$BUCKLE_ROOT/.updated
    make_null_command belt-do-nothing

	touch -d "60 minutes ago" $updated_path
	last_timestamp=$(stat -c %Y $updated_path)
	BUCKLE_TOOLBELT_NAME=belt buckle --no-update do-nothing
	[[ "$(stat -c %Y $updated_path)" = $last_timestamp ]]
}

@test "'belt --update-freq <seconds> <command>' updates with the given frequency" {
	export BUCKLE_ROOT=$BATS_TEST_DIRNAME/..
	updated_path=$BUCKLE_ROOT/.updated
    make_null_command belt-do-nothing

	touch -d "5 minutes ago" $updated_path
	last_timestamp=$(stat -c %Y $updated_path)
	BUCKLE_TOOLBELT_NAME=belt buckle --update-freq 300 do-nothing
	[[ "$(stat -c %Y $updated_path)" != $last_timestamp ]]
}

@test "buckle warns the user if the machine time offset by at least 120 seconds" {
	clock_checked_path=$TMPDIR/.buckle_clock_last_checked
	rm -f $clock_checked_path
    make_null_command belt-do-nothing

	eval "$(python-libfaketime)"
	stderr=$(FAKETIME=-120 BUCKLE_TOOLBELT_NAME=belt buckle do-nothing 2>&1 >/dev/null)
	[[ $stderr == *"The system clock is behind by"* ]]
}

@test "buckle deletes the .buckle_clock_last_checked file if clock is out of date" {
	clock_checked_path=$TMPDIR/.buckle_clock_last_checked
	rm -f $clock_checked_path
    make_null_command belt-do-nothing

	eval "$(python-libfaketime)"
	FAKETIME=-120 BUCKLE_TOOLBELT_NAME=belt buckle do-nothing 2>&1 >/dev/null
	[ ! -f $clock_checked_path ]
}

@test "buckle checks the system time no more than once every 10 minutes" {
	clock_checked_path=$TMPDIR/.buckle_clock_last_checked
	rm -f $clock_checked_path
    make_null_command belt-do-nothing

	touch -d "7 minutes ago" $clock_checked_path
	last_timestamp=$(stat -c %Y $clock_checked_path)
	BUCKLE_TOOLBELT_NAME=belt buckle do-nothing
	[[ "$(stat -c %Y $clock_checked_path)" = $last_timestamp ]]

	touch -d "10 minutes ago" $clock_checked_path
	last_timestamp=$(stat -c %Y $clock_checked_path)
	BUCKLE_TOOLBELT_NAME=belt buckle do-nothing
	[[ "$(stat -c %Y $clock_checked_path)" != $last_timestamp ]]
}

@test "buckle automatically updates itself from the remote repo" {
	_setup_test_directory TEST_DIR
	branch=$(git rev-parse --abbrev-ref HEAD)
	unset BUCKLE_ROOT

	# Create a "remote" repo with a new version of belt
	git clone . $TEST_DIR/buckle-remote
	pushd $TEST_DIR/buckle-remote
	echo "#!/usr/bin/env bash" > bin/buckle
	echo "echo my-updated-buckle \$*" >> bin/buckle
	git config user.email "test@example.com"
	git config user.name "test"
	git add bin/buckle
	git commit -m 'Test'
	popd

	# Create a clone of the original repo without the change but with the "remote" as the origin
	git clone . $TEST_DIR/buckle

	# Run belt in the clone
	cd $TEST_DIR/buckle
	git remote rm origin
	git remote add origin $TEST_DIR/buckle-remote

	virtualenv .venv
	source .venv/bin/activate
	pip install -e .

    make_null_command belt-do-nothing
	actual=$(BUCKLE_TOOLBELT_NAME=belt buckle --some-new-flag-that-does-not-exist-yet do-nothing)
	[[ $actual = "my-updated-buckle --some-new-flag-that-does-not-exist-yet do-nothing" ]]
}
