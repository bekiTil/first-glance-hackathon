# One image, two Railway services:
#   web    (SERVICE=web, default): API + built React site
#   agents (SERVICE=agents):       scheduler + job queue

FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-fund --no-audit
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock backend/.python-version ./
RUN uv sync --frozen --no-dev
COPY backend/ ./
COPY --from=web /web/dist /app/frontend/dist

ENV SERVICE=web PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "if [ \"$SERVICE\" = agents ]; then exec uv run --no-sync python -m app.worker; else exec uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port ${PORT}; fi"]
