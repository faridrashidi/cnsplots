help:
	@echo "available commands"
	@echo " - lint         : run linting and flaking"
	@echo " - test         : run all unit tests"
	@echo " - install      : install the package"

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
	pip install -e libraries/PyComplexHeatmap
	pip install -e libraries/statannotations
	python -m pip install .
