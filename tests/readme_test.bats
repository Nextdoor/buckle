#!/usr/bin/env bats

load test_helpers

setup() {
	_setup_nd_alias
}

@test "'nd readme' prints the raw readme file in non-interactive mode" {
    actual="$(echo | nd readme)"
    expected="$(cat $BATS_TEST_DIRNAME/../README.md)"
    [[ "$actual" = "$expected" && -n "$actual" ]]
}
