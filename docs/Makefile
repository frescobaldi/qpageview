# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = qpageview
SOURCEDIR     = source
BUILDDIR      = build


# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Website and Upload targets (added by WB)
# This uses the conf.py in the web/ directory
WEBDIR        = web
WEBBUILDDIR   = web/build
website:
	@$(SPHINXBUILD) -M clean "$(SOURCEDIR)" "$(WEBBUILDDIR)" -c "$(WEBDIR)" $(SPHINXOPTS) $(O)
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(WEBBUILDDIR)" -c "$(WEBDIR)" $(SPHINXOPTS) $(O)

upload: website
	rsync -ave ssh --exclude '*~' \
		"$(WEBBUILDDIR)"/html/* \
		wilbertb@qpageview.org:/home/wilbertb/domains/qpageview.org/public_html/

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
