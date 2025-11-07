# ---------- Frontend build stage ----------
FROM node:20-alpine AS frontend
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
FROM python:3.11-slim AS backend


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*


# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip wheel setuptools \
 && pip install --no-cache-dir --only-binary=:all: numpy pandas \
 && pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Bring in built frontend assets
COPY --from=frontend /app/react-app/dist ./react-app/dist

EXPOSE 5000
CMD ["python", "app.py"]