# Jeden Dockerfile, tri fázy (stage). docker-compose.override.yml používa fázu "dev",
# produkčný beh (len docker-compose.yml) poslednú fázu s nginx.

# Vývoj: Vite dev server s okamžitým obnovovaním. Počúva na porte 80 rovnako ako nginx,
# takže docker-compose.yml môže mať pre oba režimy to isté mapovanie portov.
FROM node:24-alpine AS dev
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 80
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "80"]

# Build: kontrola typov a produkčné súbory do dist/.
FROM dev AS build
RUN npm run build

# Produkcia: nginx len posiela hotové statické súbory, Node.js tu už netreba.
FROM nginx:1.27-alpine
# nginx.conf je šablóna: pri štarte do nej obraz nginx dosadí premenné prostredia
# a výsledok uloží ako /etc/nginx/conf.d/default.conf. Tu sú predvolené hodnoty pre docker compose,
# Railway ich prepíše vlastnými (PORT nastaví sám, API_UPSTREAM ty v nastaveniach služby).
# NGINX_ENTRYPOINT_LOCAL_RESOLVERS: obraz nginx pri štarte zistí DNS server kontajnera
# a dá ho do premennej NGINX_LOCAL_RESOLVERS, ktorú používa nginx.conf (resolver).
ENV PORT=80 \
    API_UPSTREAM=http://api:8000 \
    NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
