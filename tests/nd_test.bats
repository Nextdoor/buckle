#!/usr/bin/env bats

@test "'nd version' matches 'nd-version'" {
  actual="$(nd version)"
  expected="$(nd-version)"
  [[ "$actual" = "$expected" && -n "$actual" ]]
}
