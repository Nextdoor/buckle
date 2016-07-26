#!/usr/bin/env bats

load test_helpers

setup() {
	_shared_setup
}

@test "'nd <command>' runs .pre hooks in 'nd-' namespace" {
	make_executable_command nd-.my-check <<- 'EOF'
		#!/usr/bin/env bash
		echo my dot file output
EOF
	make_executable_command nd-my-command <<- 'EOF'
		#!/usr/bin/env bash
		echo my command output
EOF

	result="$(nd my-command)"
	[[ "$result" = $'my dot file output\nmy command output' ]]
}

@test "'nd <dot command>' does not run dot commands prior to running" {
	make_executable_command nd-.my-first-check <<- 'EOF'
		#!/usr/bin/env bash
		echo my first dot file output
EOF
	make_executable_command nd-.my-second-check <<- 'EOF'
		#!/usr/bin/env bash
		echo my second dot file output
EOF

	result="$(nd .my-first-check)"
	[[ "$result" = "my first dot file output" ]]
}
