FROM python:3.12-slim

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential cmake curl openjdk-21-jre-headless \
    && curl -Ls https://install.lf-lang.org | bash -s cli --prefix=/usr/local \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

WORKDIR /app

# Build with the parent directory as context; the dependencies are sibling checkouts.
ARG PROJECT_DIR=LinguaFrancaWarehouse
COPY ${PROJECT_DIR}/pyproject.toml ${PROJECT_DIR}/poetry.lock ./
COPY machine-data-model/ /machine-data-model/
COPY frost-planner/ /frost-planner/

RUN poetry install --only main --no-root

COPY ${PROJECT_DIR}/ ./

RUN lfc src/FactoryMain.lf

CMD ["python", "src-gen/FactoryMain/FactoryMain.py"]
