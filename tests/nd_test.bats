#!/usr/bin/env bats

load test_helpers

setup() {
	_shared_setup
}

@test "'nd version' matches 'nd-version'" {
	actual="$(nd version)"
	expected="$(nd-version)"
	[[ "$actual" = "$expected" && -n "$actual" ]]
}

@test "'nd init -' returns 0 exit code" {
	actual="$(nd init -)"
	expected="$(cat $BATS_TEST_DIRNAME/../nd_toolbelt/nd-init.sh)"
	[[ "$actual" = "$expected" && -n "$expected" ]]
}

@test "'nd <command>' runs 'nd-<command>'" {
	make_executable_command nd-my-command <<- 'EOF'
		#!/usr/bin/env bash
		echo "$*"
EOF

	result="$(nd my-command -a -b -c --f test)"
	echo $result
	[[ "$result" = "-a -b -c --f test" ]]
}

@test "'nd <namespace>' runs 'nd-help <namespace>'" {
	make_executable_command nd-my-namespace~my-command <<- 'EOF'
		#!/usr/bin/env bash
		echo my help output
EOF
	actual="$(nd my-namespace)"
	expected="$(nd-help my-namespace)"
	[[ "$actual" = "$expected" && "$actual" = *"my help output"* ]]
}

@test "'nd <namespace> <command>' runs 'nd-<namespace>~<command>'" {
	make_executable_command nd-my-namespace~my-command <<- 'EOF'
		#!/usr/bin/env bash
		echo "$*"
EOF

	result="$(nd my-namespace my-command -a -b -c --f arg)"
	[[ "$result" = "-a -b -c --f arg" ]]
}

@test "nd toolbelt rejects options not handled" {
	run nd -random-test-option version
	[[ $status != 0 ]]
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
