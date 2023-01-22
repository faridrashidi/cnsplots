help:
	@echo "available commands"
	@echo " - lint         : run linting and flaking"
	@echo " - test         : run all unit tests"
	@echo " - install      : install the package"

lint:
	pre-commit run --all-files

test:
	pytest --disable-warnings ./tests

install:
	python -m pip install .
