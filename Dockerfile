FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
COPY src ./src
COPY docs ./docs

RUN uv sync --no-dev

ENV MATRIX_OPEN_BROWSER=0
EXPOSE 8765

CMD ["uv", "run", "matrix-jack-in", "--no-browser"]
