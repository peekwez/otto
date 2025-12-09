FROM python:3.12-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Install system and build dependencies
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libavcodec-extra \
        curl \
        ca-certificates \
        build-essential \
        git \
        libpq-dev \
        && apt-get clean && rm -rf /var/lib/apt/lists/*


# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv* /usr/local/bin/

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./

# Install dependencies (will respect uv.lock and install into /install)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy only necessary source code and certs for modularity and caching
COPY src/ src/

# Add other necessary directories as needed (e.g., atlas/, components/ if required)
RUN uv sync --frozen --no-dev

# ---------- Stage 2: Runtime environment ----------
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install runtime system packages
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
        git \
        libavcodec-extra \
        ca-certificates \
        libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY --from=builder /app/src /app/src
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

# Add other necessary directories as needed
RUN mkdir -p /app/data

EXPOSE 8000

# Run the FastAPI Server
CMD ["otto", "app", "--host", "0.0.0.0", "--port", "8000"]
