FROM docker.io/nginx:1.25

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/nginx.conf
COPY ./letsencrypt/ /etc/letsencrypt

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
