FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
COPY src ./src
COPY docs ./docs

RUN uv sync --no-dev

ENV MATRIX_OPEN_BROWSER=0
ENV MATRIX_DASHBOARD_HOST=0.0.0.0
ENV REDIS_URL=redis://redis:6379/0
EXPOSE 8765

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/status', timeout=2)" || exit 1

CMD ["uv", "run", "matrix-jack-in", "--no-browser"]
