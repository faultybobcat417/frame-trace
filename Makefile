.PHONY: doctor demo test dev models verify

doctor:
	frame-trace doctor

demo:
	frame-trace demo

test:
	pytest
	cd frontend && npm test

dev:
	./scripts/dev.sh

models:
	python scripts/fetch_models.py

verify:
	./scripts/verify_release.sh
