# Reproducible runtime for the pipeline. Python and every dependency are pinned by uv.lock.
FROM python:3.12.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_PROJECT_ENVIRONMENT=/opt/venv
COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --all-groups --frozen --no-install-project

COPY . .
RUN cd dbt && uv run dbt deps --profiles-dir .

ENV GSS_DB_PATH=/app/data/gss.duckdb GSS_LOG_DIR=/app/logs
ENTRYPOINT ["uv", "run", "python", "-m", "source.pipeline.run"]
