FROM python:3-slim as base

RUN apt-get update && apt-get install -y --no-install-recommends \
  git \
  && rm -rf /var/lib/apt/lists/*

FROM base as python-build

WORKDIR /usr/src/app

COPY README.md .
COPY requirements.txt .
COPY pyproject.toml .
COPY src ./src

RUN python -m venv /venv

RUN /venv/bin/pip install --no-cache-dir .

FROM python:3-slim

COPY --from=python-build /venv /venv
ENV PATH=/venv/bin:$PATH
