# Entry points for the GSS religiosity & media pipeline. Every target is safe to re-run.
# Requires uv (https://docs.astral.sh/uv/). `make help` lists targets.

UV ?= uv
export GSS_DB_PATH ?= $(CURDIR)/data/gss.duckdb

.PHONY: report-pdf help setup pipeline load seed build test analyses docs serve-docs lint test-python clean verify-raw docker-build docker-run

help:            ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

setup:           ## create the pinned virtual environment and install dbt packages
	$(UV) sync --all-groups --frozen
	cd dbt && $(UV) run dbt deps --profiles-dir .

verify-raw:      ## check the committed raw extracts against their SHA-256 manifest
	cd source/data/raw && shasum -a 256 -c MANIFEST.sha256

pipeline:        ## run everything: load -> seed -> build (models + tests) -> analyses -> docs
	$(UV) run python -m source.pipeline.run

load:            ## load the raw extracts into DuckDB (idempotent)
	$(UV) run python -m source.pipeline.run --only load

seed:            ## load dbt seeds (metadata)
	$(UV) run python -m source.pipeline.run --only seed

build:           ## dbt build: models and tests
	$(UV) run python -m source.pipeline.run --only build

test:            ## dbt tests only (models must already exist)
	cd dbt && $(UV) run dbt test --profiles-dir .

analyses:        ## run the six questions + overlap audit, write docs/analysis_results/
	$(UV) run python -m source.pipeline.run --only analyses

docs:            ## generate dbt documentation
	$(UV) run python -m source.pipeline.run --only docs

serve-docs:      ## open the dbt docs site locally
	cd dbt && $(UV) run dbt docs serve --profiles-dir .

test-python:     ## loader unit/idempotency tests
	$(UV) run pytest -q

lint:            ## ruff (python) and sqlfluff (dbt SQL)
	$(UV) run ruff check source
	cd dbt && $(UV) run sqlfluff lint models analyses tests --dialect duckdb

profile:         ## regenerate docs/data_profile_tables.md from the raw JSON (stdlib only)
	python3 -I source/profile/profile_raw_extracts.py

seeds-regenerate: ## regenerate the code-list seeds from the raw extract metadata
	$(UV) run python -m source.metadata.build_seeds

clean:           ## remove the local database, logs and dbt artefacts
	rm -f data/*.duckdb data/*.duckdb.wal
	rm -rf logs dbt/target dbt/logs

docker-build:    ## build the reproducible image
	docker build -t gss-religiosity-media .

docker-run:      ## run the full pipeline inside the image; results land in ./data, ./logs, ./docs
	docker run --rm -v "$(CURDIR)/data:/app/data" -v "$(CURDIR)/logs:/app/logs" -v "$(CURDIR)/docs/analysis_results:/app/docs/analysis_results" gss-religiosity-media

report-pdf:      ## render report/report.md to report/report.pdf (needs pandoc and Google Chrome)
	sed 's/\\newpage/<div style="page-break-before: always"><\/div>/' report/report.md > /tmp/gss_report.md
	pandoc /tmp/gss_report.md -s --css report/report.css --embed-resources -o /tmp/gss_report.html
	"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf=report/report.pdf file:///tmp/gss_report.html
