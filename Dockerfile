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

# Copy the built wheel artifact and install it into the builder virtualenv.
COPY dist /dist
RUN set -eux; \
    set -- /dist/gitlabform-*.whl; \
    if [ "$#" -ne 1 ]; then \
      echo "Expected exactly one gitlabform wheel under /dist, found $#"; \
      exit 1; \
    fi; \
    uv pip install --python /app/.venv/bin/python "$1"

# ---- Final Stage ----
FROM python:3.14-alpine AS final

LABEL org.opencontainers.image.title="GitLabForm" \
      org.opencontainers.image.description="GitLabForm is a declarative GitLab configuration management tool." \
      org.opencontainers.image.vendor="gitlabform" \
      org.opencontainers.image.licenses="MIT"

# Create a non-root user for security
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy the virtual environment to the same location to preserve absolute paths in shebangs
COPY --from=builder /app/.venv /app/.venv

# Update PATH to include the virtual environment's bin directory
ENV PATH="/app/.venv/bin:$PATH"

# Set the user to the non-root user and the working directory
USER appuser
WORKDIR /config
