.PHONY: install test demo lint run compare clean

VENV ?= .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

test:
	$(PY) -m pytest -q

lint:
	$(VENV)/bin/ruff check .

run:
	$(PY) -m llmqa run --provider mock --profile good

demo:
	$(PY) -m llmqa demo-failures

compare:
	$(PY) -m llmqa compare --baseline baselines/baseline.json --current reports/latest.json

clean:
	rm -rf reports/*.json reports/*.md .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
