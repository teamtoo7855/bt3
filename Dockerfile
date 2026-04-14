FROM ghcr.io/astral-sh/uv:alpine
# Copy the project into the image
COPY . /app

# Disable development dependencies
ENV UV_NO_DEV=1

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked
EXPOSE 8080
CMD ["uv", "run", "src/app.py"]