# ── Nginx alpine para servir archivos estáticos ──
FROM nginx:alpine

# Quitar la config por defecto de nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copiar configuración personalizada
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar los archivos del frontend
COPY . /usr/share/nginx/html

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]