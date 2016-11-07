#!/usr/bin/env bats

load test_helpers

setup() {
	_setup_alias belt
}

@test "'belt readme' prints the raw readme file in non-interactive mode" {
    actual="$(echo | belt readme)"
    expected="$(cat $BATS_TEST_DIRNAME/../README.md)"
    [[ "$actual" = "$expected" && -n "$actual" ]]
}
