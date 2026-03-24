FROM node:20-slim AS build

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-slim

RUN npm install -g serve

WORKDIR /app
COPY --from=build /app/dist ./dist

ENV PORT=3000
EXPOSE $PORT

CMD ["sh", "-c", "serve dist -l $PORT -s"]
