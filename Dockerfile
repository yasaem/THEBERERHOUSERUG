ARG DEPENDENCY_STAGE=online
FROM python:3.12-slim AS runtime-base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 BAZAR_DB=/data/bazar.sqlite3 PORT=3000
WORKDIR /app
RUN groupadd --gid 10001 bazar && useradd --uid 10001 --gid 10001 --create-home bazar && mkdir /data /backups && chown bazar:bazar /data /backups

FROM runtime-base AS online
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Optional verified wheel download for build hosts without outbound DNS.
FROM runtime-base AS offline
COPY requirements.txt .
COPY .build/wheels/ /wheels/
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && rm -rf /wheels

FROM ${DEPENDENCY_STAGE} AS application
COPY --chown=bazar:bazar server.py payroll.py saas.py documents.py localization.py wsgi.py gunicorn.conf.py ./
COPY --chown=bazar:bazar static/ ./static/
COPY --chown=bazar:bazar scripts/ ./scripts/
COPY --chown=bazar:bazar tests/ ./tests/
COPY --chown=bazar:bazar docs/ ./docs/
COPY --chown=bazar:bazar README.md README_EN.md ./
USER 10001:10001
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','3000')+'/healthz',timeout=3)"
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:application"]
