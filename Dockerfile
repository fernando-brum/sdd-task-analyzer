# Imagem de execução isolada do Test Harness do TaskAnalyzer.
# Contrato: seção 5.3 de specs/task_analyzer_spec.md (v1.2).
# Regras: DI-01 (base fixa), DI-03 (mesmo pytest.ini), DI-04 (não-root),
# DI-05 (dependências só do requirements.txt) e PR-07 (sem segredos).

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --root-user-action=ignore -r requirements.txt

RUN useradd --create-home --uid 1000 analyzer \
    && chown analyzer:analyzer /app

COPY --chown=analyzer:analyzer pytest.ini .
COPY --chown=analyzer:analyzer src/ src/
COPY --chown=analyzer:analyzer tests/ tests/

USER analyzer

CMD ["pytest", "tests/test_harness.py", "-v"]
