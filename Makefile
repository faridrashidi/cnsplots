help:
	@echo "available commands"
	@echo " - lint         : run linting and flaking"
	@echo " - test         : run all unit tests"
	@echo " - install      : install the package"

clean:
	rm -rf docs/build
	rm -rf htmlcov
	rm -rf .coverage*
	rm -rf docs/cnsplots*
	rm -rf docs/auto_examples
	rm -rf docs/gen_modules

lint:
	pre-commit run --all-files

test:
	pytest --disable-warnings ./tests

doc:
	rm -rf docs/source/cnsplots*
	rm -rf docs/source/auto_examples
	rm -rf docs/source/gen_modules
	cd docs && $(MAKE) clean html
	cd docs/build/html && python -m http.server 8080

install:
	python -m pip install .
