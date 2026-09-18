# =============================================================================
# CareerMate Market Intelligence — Frontend Dashboard Container
# Multi-stage production build: Node.js build -> Nginx Alpine runtime
# =============================================================================

FROM node:18-alpine AS build

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install --silent

# Build production assets
COPY . ./
ARG REACT_APP_API_URL=http://localhost:8001
ENV REACT_APP_API_URL=${REACT_APP_API_URL}
RUN npm run build

# Runtime Stage: Lightweight Nginx
FROM nginx:alpine AS runtime

COPY --from=build /app/build /usr/share/nginx/html

# SPA fallback configuration for React Router
RUN echo 'server {' \
    '    listen 3000;' \
    '    location / {' \
    '        root /usr/share/nginx/html;' \
    '        index index.html index.htm;' \
    '        try_files $uri $uri/ /index.html;' \
    '    }' \
    '}' > /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
