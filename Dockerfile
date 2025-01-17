FROM python:3.13-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Use the system Python because we're in a container
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

# Add the uv files
COPY uv.lock pyproject.toml .python-version /app/

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --compile-bytecode
    
# Add the rest of the files
ADD . /app/

# Set the path to the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

CMD [ "python", "bot.py" ]