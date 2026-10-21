# HR Library — the two commands that matter.
#
#   make build   generate _site/ from content/
#   make check   build, then run every gate
#
# `make check` is the gate. It must exit 0 before work is called done.
# Windows with no make: run the two commands under it directly.

PYTHON ?= python3
# The console on the owner's machine is cp1252 and chokes on ₦.
export PYTHONIOENCODING = utf-8

.PHONY: build check audit docx clean

build:
	$(PYTHON) tools/sitegen/sitegen.py

audit: build
	$(PYTHON) tools/sitegen/audit.py

docx:
	$(PYTHON) tools/sitegen/docx_regression.py

check: audit docx

clean:
	rm -rf _site _audit_text
