# Stage 1: Build React Application
FROM node:24-slim AS builder

WORKDIR /app

COPY package.json /app/
RUN npm install --legacy-peer-deps

COPY . /app/
RUN npm run build

# Stage 2: Serve React via Nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# Custom nginx configuration (optional, defaults are fine for simple SPA routing)
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
