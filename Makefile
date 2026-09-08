VALID_RELEASE_PARTS := patch minor major
RELEASE_ARGS := $(filter-out release,$(MAKECMDGOALS))

help:
	@echo "available commands"
	@echo " - clean        : clean the repo"
	@echo " - lint         : run linting and flaking"
	@echo " - test         : run all unit tests"
	@echo " - test-branches: report statement and branch coverage separately"
	@echo " - test-visual  : run visual regression tests"
	@echo " - doc          : build the documentation"
	@echo " - doc-serve    : build and serve documentation on port 8080"
	@echo " - doc-linkcheck: check documentation links"
	@echo " - install      : install the full development environment and hooks"
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
	uv run --locked --extra lint pre-commit run --all-files

test:
	uv run --locked --extra test pytest ./tests

.PHONY: test-branches

test-branches:
	COVERAGE_FILE=.coverage.branches uv run --locked --extra test pytest ./tests --cov-branch --cov-fail-under=0 --cov-report=json:.coverage.branches.json
	uv run --locked --extra test python tools/report_coverage.py .coverage.branches.json

test-visual:
	uv run --locked --extra test pytest tests/test_visual_regressions.py --mpl --no-cov

.PHONY: doc doc-serve doc-linkcheck

doc:
	$(MAKE) -C docs clean
	cd docs && $(MAKE) html

doc-serve: doc
	uv run --locked --extra docs python -m http.server 8080 --directory docs/build/html

doc-linkcheck:
	cd docs && $(MAKE) linkcheck

install:
	uv sync --locked --extra dev
	uv run --locked --extra lint pre-commit install

release:
	@if [ "$(words $(RELEASE_ARGS))" -ne 1 ] || [ -n "$(filter-out $(VALID_RELEASE_PARTS),$(RELEASE_ARGS))" ]; then \
		echo "usage: make release [patch|minor|major]"; \
		exit 1; \
	fi
	uv run --locked --extra release bump-my-version bump $(RELEASE_ARGS)

patch minor major:
	@:
