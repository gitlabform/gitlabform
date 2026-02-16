# ---- Builder Stage ----
FROM python:3.12-alpine AS builder

# Set the working directory
WORKDIR /app

# Install build-time dependencies
RUN apk add --no-cache build-base

# Copy dependency definitions to leverage Docker's layer cache
COPY pyproject.toml ./

# Install dependencies. This layer will be cached as long as pyproject.toml does not change.
RUN pip install --no-cache-dir --prefix=/install .

# Now copy the application source code and install the application itself
COPY gitlabform ./gitlabform
# Install the application code itself. Dependencies are already in the cached layer above,
# so we use --no-deps to make it faster and the intent clear.
RUN pip install --no-deps --no-cache-dir --prefix=/install .

# ---- Final Stage ----
FROM python:3.12-alpine AS final

# Create a non-root user for security
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy the installed artifacts from the builder stage
COPY --from=builder /install /usr/local

# Set the user to the non-root user
USER appuser

# Set the working directory for the application to run
WORKDIR /config
