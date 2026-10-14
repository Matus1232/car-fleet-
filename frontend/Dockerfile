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
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
