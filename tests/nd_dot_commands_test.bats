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
