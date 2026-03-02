# ---------- Frontend build stage ----------
FROM node:20-alpine AS frontend
WORKDIR /app/react-app

# Install dependencies first for better caching
COPY react-app/package.json react-app/package-lock.json ./
RUN npm ci

# Copy source and build
COPY react-app/ .
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

# ---------- Python dependencies stage ----------
FROM python:3.11-slim AS pydeps
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app

COPY requirements.txt ./
RUN python -m venv "$VIRTUAL_ENV" \
 && pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

# ---------- Backend runtime stage ----------
FROM python:3.11-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app

# Copy Python virtualenv from builder stage
COPY --from=pydeps /opt/venv /opt/venv

# Copy only runtime backend files
COPY app.py ./
COPY analyse_search.py ./
COPY config.py ./
COPY db_connection.py ./
COPY dash_app.py ./
COPY flask_cache.py ./
COPY get_assessment.py ./
COPY log_events.py ./
COPY dash_pages ./dash_pages
COPY migrations ./migrations

# Bring in built frontend assets
COPY --from=frontend /app/react-app/dist ./react-app/dist

EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "--timeout", "60", "app:app"]
