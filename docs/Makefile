# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
# Run Sphinx through uv so `make html` uses the project's development extra.
SPHINXBUILD   ?= uv run --extra dev sphinx-build
STAGEDBUILD   ?= uv run --extra dev python _scripts/build_versioned_docs.py
SOURCEDIR     = .
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help clean html linkcheck Makefile

clean:
	rm -rf "$(BUILDDIR)"

html:
	@$(STAGEDBUILD) --builder html "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)

linkcheck:
	@$(STAGEDBUILD) --builder linkcheck "$(BUILDDIR)/linkcheck" $(SPHINXOPTS) $(O)

# Catch-all target: stage every Sphinx builder so generated sources stay in build.
%: Makefile
	@$(STAGEDBUILD) --builder $@ "$(BUILDDIR)/$@" $(SPHINXOPTS) $(O)
