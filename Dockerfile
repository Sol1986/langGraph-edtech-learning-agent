# The Foundation language/runtime
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS runner

# The Folder Where files live inside the container
WORKDIR /app

# Copy ONLY the dependency files first (optimizes Docker caching)
COPY pyproject.toml uv.lock ./

# Install the project's dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the application code, then install the project itself
COPY src/ ./src

COPY README.md ./
# Install the project itself (so `company_research_agent` is importable)
#  This tells Docker to execute a terminal command during the build phase using the uv tool.
# uv sync: This command creates a virtual environment and installs all the dependencies listed in your project configuration files
# --frozen: This locks down your dependencies.
# --no-dev: This excludes any development dependencies from being installed, ensuring that only the necessary packages for running the application are included in the final image.
RUN uv sync --frozen --no-dev

# Make the synced virtualenv's binaries (uvicorn, etc.) the default on PATH
ENV PATH="/app/.venv/bin:$PATH"

# CRITERIA: "Avoid running containers as root user"
USER guest
EXPOSE 8000

# Run the application using uv's virtual environment
# Setting it to 0.0.0.0 allows your local computer or cloud routers to successfully talk to all available network interfaces inside the container.
#  This instructs Uvicorn to listen for traffic specifically on port 8000 inside the container network. 
CMD ["uvicorn", "company_research_agent.api.app:app", "--host", "0.0.0.0", "--port", "8000"]