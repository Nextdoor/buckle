setup_tests:
	git clone https://github.com/sstephenson/bats.git

test:
	bats/bin/bats tests/*.bats
