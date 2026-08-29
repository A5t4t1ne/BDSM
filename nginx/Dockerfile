FROM docker.io/nginx:1.25

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/nginx.conf

# Certificates are NOT copied in: baking a private key into an image layer
# leaks it to anyone who can pull the image, and the key could never be
# renewed without a rebuild. They are bind-mounted at runtime instead
# (see docker-compose.yaml).

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
