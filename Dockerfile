FROM node:24.21.0-alpine AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.13.15-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN python -m pip install --no-cache-dir -r backend/requirements.txt \
    && groupadd --system voluntia && useradd --system --gid voluntia voluntia
COPY backend/ backend/
COPY database/ database/
COPY --from=frontend /build/frontend/dist/voluntia-frontend/browser/ frontend/dist/voluntia-frontend/browser/
RUN mkdir -p /app/.local/storage && chown -R voluntia:voluntia /app/.local
USER voluntia
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/api/health',timeout=3)"
CMD ["python", "-m", "backend.app.serve"]
