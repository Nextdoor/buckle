ifndef TERM
    # Don't use pretty format if terminal is not available
    BATS_FLAGS = -t
endif

test:
	bats/bin/bats $(BATS_FLAGS) tests/*.bats

bats:
	git clone https://github.com/sstephenson/bats.git

init: bats
	-flake8 --install-hook  # allow this line to fail
	pip install -r requirements.txt
