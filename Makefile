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
	rm -rf docs/auto_examples
	rm -rf docs/gen_modules

lint:
	pre-commit run --all-files

test:
	pytest --disable-warnings ./tests

serve:
	cd docs/build/html && python -m http.server 8080

doc:
	rm -rf docs/build
	rm -rf docs/cnsplots*
	rm -rf docs/auto_examples
	rm -rf docs/gen_modules
	cd docs && $(MAKE) clean html
	cd docs/build/html && python -m http.server 8080

install:
	python -m pip install .
	pre-commit install
