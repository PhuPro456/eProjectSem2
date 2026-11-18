# Build context MUST be the repository root:
#     docker compose build frontend
#     docker build -f frontend/Dockerfile .
# Run `npm run build` in frontend/ first: the image ships the compiled SPA
# (dist/ also contains static/covers, copied there by the Vite build).
FROM nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
