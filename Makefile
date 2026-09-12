.PHONY: install test check verify report refine init clean docs-serve docs-build install-docs

install:
	pip install -e ".[dev]"

init:
	aah init

check:
	aah check --strict

verify:
	aah verify --log-file .aegis/logs/audit-trail.jsonl
	aah verify --log-file .aegis/logs/forensic-trail.jsonl

report:
	aah report -o .aegis/reports/audit-report.md

refine:
	aah refine

test:
	pytest -v tests/

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache site/

install-docs:
	pip install -e ".[docs]"

docs-serve:
	mkdocs serve

docs-build:
	mkdocs build --strict
