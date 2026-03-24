FROM node:20-slim AS build

ARG VITE_API_URL=https://backend-production-e9d7.up.railway.app/api
ENV VITE_API_URL=$VITE_API_URL

ARG VITE_DEMO_MODE=true
ENV VITE_DEMO_MODE=$VITE_DEMO_MODE

ARG VITE_INTERCOM_APP_ID=
ENV VITE_INTERCOM_APP_ID=$VITE_INTERCOM_APP_ID

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
