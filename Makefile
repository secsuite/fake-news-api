VENV ?= .venv
PYTHON := $(VENV)/bin/python
BLACK := $(VENV)/bin/black
RUFF := $(VENV)/bin/ruff
MYPY := $(VENV)/bin/mypy
PYTEST := $(VENV)/bin/pytest
PRE_COMMIT := $(VENV)/bin/pre-commit
PYTEST_WORKERS ?= 1

.PHONY: install-runtime install-dev-lite install-dev quality-lite quality quality-fix test-fast test-integration precommit

install-runtime:
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

install-dev-lite:
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install \
		black==24.10.0 \
		ruff==0.6.8 \
		mypy>=1.10.0 \
		pre-commit>=3.7.0

install-dev: install-runtime
	$(PYTHON) -m pip install -e ".[dev]"
	$(PRE_COMMIT) install --hook-type pre-commit --hook-type pre-push

quality-lite:
	$(BLACK) --check app tests
	$(RUFF) check app tests
	$(MYPY) app tests

quality:
	$(MAKE) quality-lite
	$(MAKE) test-fast

quality-fix:
	$(BLACK) app tests
	$(RUFF) check app tests --fix
	$(MYPY) app tests
	$(MAKE) test-fast

test-fast:
	$(PYTEST) -q --maxfail=1 $(if $(filter 1,$(PYTEST_WORKERS)),,-n $(PYTEST_WORKERS)) -m "not integration"

test-integration:
	$(PYTEST) -q --maxfail=1 -m "integration"

precommit:
	$(PRE_COMMIT) run --all-files
