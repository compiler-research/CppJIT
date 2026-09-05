#!/usr/bin/env bash
# Smoke first to fail fast, then the full suite, against the installed
# cppjit. Run from the repository (or cibuildwheel test-sources) root;
# shared by the cibuildwheel test phase and the relocation and sdist jobs.
set -e
export CPPINTEROP_EXTRA_INTERPRETER_ARGS=-std=c++20
python -X faulthandler .github/wheel_smoke.py
cd test
make -j"$(python -c 'import os; print(os.cpu_count())')" PYTHON=python
python -m pytest -ra
