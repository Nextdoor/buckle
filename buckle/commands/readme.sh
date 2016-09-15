#!/bin/bash
TEST_DIRECTORY="$(mktemp -d buckle_readme.XXXXX --tmpdir)"
trap "rm -rf $TEST_DIRECTORY" EXIT
cd $TEST_DIRECTORY

# Install a markdown viewer that happens to be called "nd" too
echo Installing markdown viewer...
npm init --yes > /dev/null && npm install nd >& /dev/null

if [[ $? = 0 ]]; then
    cat $1 | PATH=$(npm bin):$PATH nd
else
    echo "failed."
fi
