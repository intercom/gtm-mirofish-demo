FROM node:20-slim AS build

ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

ARG VITE_DEMO_MODE=true
ENV VITE_DEMO_MODE=$VITE_DEMO_MODE

ARG VITE_INTERCOM_APP_ID=
ENV VITE_INTERCOM_APP_ID=$VITE_INTERCOM_APP_ID

ARG VITE_AUTH_ENABLED=true
ENV VITE_AUTH_ENABLED=$VITE_AUTH_ENABLED

ARG VITE_AUTH_ALLOWED_DOMAIN=intercom.io
ENV VITE_AUTH_ALLOWED_DOMAIN=$VITE_AUTH_ALLOWED_DOMAIN

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

COPY . .
RUN pnpm run build

FROM node:20-slim

RUN npm install -g serve

WORKDIR /app
COPY --from=build /app/dist ./dist

ENV PORT=3000
EXPOSE $PORT

CMD ["sh", "-c", "serve dist -l $PORT -s"]
