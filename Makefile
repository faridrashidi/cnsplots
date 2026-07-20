VALID_RELEASE_PARTS := patch minor major
RELEASE_ARGS := $(filter-out release,$(MAKECMDGOALS))

help:
	@echo "available commands"
	@echo " - clean        : clean the repo"
	@echo " - lint         : run linting and flaking"
	@echo " - test         : run all unit tests"
	@echo " - doc          : build the documentation"
	@echo " - doc-linkcheck: check documentation links"
	@echo " - install      : install the package"
	@echo " - release      : bump version with [patch|minor|major]"

clean:
	rm -rf htmlcov
	rm -rf .coverage*
	rm -rf coverage.xml
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf .tox
	rm -rf .nox
	rm -rf .hypothesis
	rm -rf build
	rm -rf dist
	rm -rf docs/build
	rm -rf docs/_build
	rm -rf docs/api
	rm -rf docs/examples
	rm -rf docs/gen_modules
	rm -rf docs/sg_execution_times.rst
	rm -rf tests/__pycache__

lint:
	uv run pre-commit run --all-files

test:
	uv run pytest ./tests

doc: clean
	cd docs && $(MAKE) html
ifneq ($(CI),true)
	cd docs/build/html && python -m http.server 8080
endif

doc-linkcheck:
	cd docs && $(MAKE) linkcheck

install:
	uv sync --extra dev
	uv run pre-commit install

release:
	@if [ "$(words $(RELEASE_ARGS))" -ne 1 ] || [ -n "$(filter-out $(VALID_RELEASE_PARTS),$(RELEASE_ARGS))" ]; then \
		echo "usage: make release [patch|minor|major]"; \
		exit 1; \
	fi
	uv run bump-my-version bump $(RELEASE_ARGS)

patch minor major:
	@:
