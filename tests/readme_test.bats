#!/usr/bin/env bats

@test "'nd readme' prints the raw readme file in non-interactive mode" {
    actual="$(echo | nd readme)"
    expected="$(cat $BATS_TEST_DIRNAME/../README.md)"
    [[ "$actual" = "$expected" && -n "$actual" ]]
}
