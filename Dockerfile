FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy shared source files
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen ensures we use the exact versions from uv.lock
RUN uv sync --frozen --no-install-project

# Install gunicorn for production serving
RUN uv pip install gunicorn

# Copy source code and readme
COPY src/ src/
COPY README.md .

# Install the project
RUN uv pip install .

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Flask Environment Variables
ENV FLASK_APP=poker_range_practice
ENV HOST=0.0.0.0
ENV PORT=5000

EXPOSE 5000

# Run the application
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "poker_range_practice:create_app()"]
