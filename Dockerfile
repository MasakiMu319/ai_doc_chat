FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml ./

RUN uv sync

COPY . .

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app /app

COPY data/ data/
COPY conf/ conf/
COPY .env .env

# 清理缓存
RUN rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["uv", "run", "main.py"]
