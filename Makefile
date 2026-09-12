.PHONY: install test check verify report refine init clean

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
	rm -rf build/ dist/ *.egg-info .pytest_cache
