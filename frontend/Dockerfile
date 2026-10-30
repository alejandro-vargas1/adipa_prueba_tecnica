# build con Node, se sirve el resultado estático con nginx
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# la URL del backend se lee de VITE_API_URL al arrancar el contenedor, no al construir la imagen
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY --chmod=755 config.sh /docker-entrypoint.d/40-config.sh
