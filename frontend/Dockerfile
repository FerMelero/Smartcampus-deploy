FROM nginx:1.27-alpine

ENV BACKEND_URL=http://backend:8000

COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY web /usr/share/nginx/html

EXPOSE 80
