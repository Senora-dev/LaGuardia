
.PHONY: install test
install:
	pip install .
test:
	pytest -q
