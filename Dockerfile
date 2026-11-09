FROM python:3.12-slim AS build

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential cmake curl openjdk-21-jre-headless \
    && curl -fsSL https://install.lf-lang.org | bash -s cli --prefix=/usr/local \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

WORKDIR /app

# Build from the parent directory so the sibling path dependencies are available.
COPY LinguaFrancaWarehouse/pyproject.toml LinguaFrancaWarehouse/poetry.lock ./
COPY machine-data-model/ /machine-data-model/
COPY frost-planner/ /frost-planner/

RUN poetry install --only main --no-root

COPY LinguaFrancaWarehouse/ ./

RUN lfc src/FactoryMain.lf \
    && rm -rf src-gen/FactoryMain/build

FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=build /app/.venv/ /app/.venv/
COPY --from=build /app/src-gen/FactoryMain/ /app/src-gen/FactoryMain/
COPY --from=build /app/models/ /app/models/
COPY --from=build /app/resources/ /app/resources/

CMD ["/app/.venv/bin/python", "src-gen/FactoryMain/FactoryMain.py"]
