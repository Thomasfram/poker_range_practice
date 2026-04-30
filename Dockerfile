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

# Copy source code and readme
COPY src/ src/
COPY README.md .

# Install the project in editable mode so volume-mounted src/ is used directly
RUN uv pip install -e .

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

ENV HOST=0.0.0.0
ENV PORT=5000
ENV SECRET_KEY=production_secret_key_change_me_in_prod

EXPOSE 5000

# Run the application
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "5000", "--factory", "poker_range_practice:create_app"]
