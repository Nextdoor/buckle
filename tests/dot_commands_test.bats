#!/usr/bin/env bats

load test_helpers

setup() {
	_shared_setup belt
}

@test "'belt <command>' runs .pre hooks in 'belt-' namespace" {
	make_executable_command belt-.my-check <<- 'EOF'
		#!/usr/bin/env bash
		echo my dot file output
EOF
	make_executable_command belt-my-command <<- 'EOF'
		#!/usr/bin/env bash
		echo my command output
EOF

	result="$(belt my-command)"
	[[ "$result" = $'my dot file output\nmy command output' ]]
}

@test "'belt <dot command>' does not run dot commands prior to running" {
	make_executable_command belt-.my-first-check <<- 'EOF'
		#!/usr/bin/env bash
		echo my first dot file output
EOF
	make_executable_command belt-.my-second-check <<- 'EOF'
		#!/usr/bin/env bash
		echo my second dot file output
EOF

	result="$(belt .my-first-check)"
	[[ "$result" = "my first dot file output" ]]
}
