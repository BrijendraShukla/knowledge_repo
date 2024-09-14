# Dockerfile for Angular frontend

# Stage 1: Build the Angular application
FROM node:20.17.0 as build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 4200
CMD ["npx", "ng", "serve","--host","0.0.0.0","--disable-host-check"]