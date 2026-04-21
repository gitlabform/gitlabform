# ---- Builder Stage ----
FROM python:3.14-alpine AS builder

# Install uv binary directly
COPY --from=ghcr.io/astral-sh/uv:0.11.2 /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Copy dependency definitions and the lockfile for reproducibility
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtualenv. This layer is cached based on uv.lock.
RUN uv sync --frozen --no-dev --no-install-project

# Now copy the application source code and install the project itself
COPY gitlabform ./gitlabform
COPY README.md ./
RUN uv sync --frozen --no-dev --no-editable

# ---- Final Stage ----
FROM python:3.14-alpine AS final

# Create a non-root user for security
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy the virtual environment to the same location to preserve absolute paths in shebangs
COPY --from=builder /app/.venv /app/.venv

# Update PATH to include the virtual environment's bin directory
ENV PATH="/app/.venv/bin:$PATH"

# Set the user to the non-root user and the working directory
USER appuser
WORKDIR /config
