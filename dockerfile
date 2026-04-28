# ---------- Frontend build stage ----------
FROM node:24-alpine AS frontend
WORKDIR /app/react-app

# Install dependencies first for better caching
COPY react-app/package.json react-app/package-lock.json ./
RUN npm ci

# Copy source and build
COPY react-app/ .
# Optional: pass at build time with --build-arg VITE_API_BASE_URL=...
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

# ---------- Backend (runtime) stage ----------
FROM python:3.14-slim AS backend


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app


# Install Python dependencies from uv lockfile
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv \
 && uv sync --frozen --no-dev --no-install-project

# Copy app source
COPY . .

# Bring in built frontend assets
COPY --from=frontend /app/react-app/dist ./react-app/dist

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "--timeout", "60", "app:app"]
