# The Foundation language/runtime
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS runner

# The Folder Where files live inside the container
WORKDIR /app

# Copy ONLY the dependency files first (optimizes Docker caching)
COPY pyproject.toml uv.lock ./

# Install the project's dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy the application code.
COPY src/ ./src

# Make the synced virtualenv's binaries (uvicorn, etc.) the default on PATH
ENV PATH="/app/.venv/bin:$PATH"

# CRITERIA: "Avoid running containers as root user"
RUN useradd --system --no-create-home --uid 10001 appuser
USER appuser

# listen to absolutely everyone and every network interface 
# if you don't specify this, servers usually only listen to 127.0.0.1 (localhost), which means only listen to requests coming from inside this exact same machine.
# Because a Docker container acts like a completely isolated mini-computer, setting it to 0.0.0.0 tells Uvicorn to accept traffic coming from outside the container (like your main computer, or the internet).
# 8000 means those visitors are all being directed specifically to Office Room 8000 on the 8th floor where your agent lives.
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]