#!/bin/sh
# nginx ejecuta los scripts de /docker-entrypoint.d/ antes de arrancar
echo "window.API_URL = \"${VITE_API_URL:-}\";" > /usr/share/nginx/html/config.js
