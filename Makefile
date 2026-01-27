help:
	@echo "available commands"
	@echo " - clean        : clean the repo"
	@echo " - lint         : run linting and flaking"
	@echo " - test         : run all unit tests"
	@echo " - serve        : open up the documentation"
	@echo " - doc          : build the documentation"
	@echo " - install      : install the package"

clean:
	rm -rf htmlcov
	rm -rf .coverage*
	rm -rf docs/build
	rm -rf docs/cnsplots*
	rm -rf docs/api
	rm -rf docs/examples
	rm -rf docs/gen_modules
	rm -rf examples/renv
	rm -rf docs/sg_execution_times.rst

lint:
	pre-commit run --all-files

test:
	pytest --disable-warnings ./tests

serve:
	cd docs/build/html && python -m http.server 8080

doc: clean
	cd docs && $(MAKE) html
	cd docs/build/html && python -m http.server 8080

install:
	uv sync --all-extras
	pre-commit install
