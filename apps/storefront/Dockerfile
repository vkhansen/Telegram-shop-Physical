# White-label Astro storefront (CARD-38) — Node SSR for Funnel / reverse-proxy
FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci || npm install

COPY . .

# Empty PUBLIC_API_BASE → browser uses same-origin (/api/public via Caddy)
# SSR uses API_INTERNAL_BASE at runtime (http://bot:9090)
ARG PUBLIC_API_BASE=
ARG PUBLIC_SITE_URL=https://telegram-shop-1.tail31319c.ts.net
ENV PUBLIC_API_BASE=$PUBLIC_API_BASE
ENV PUBLIC_SITE_URL=$PUBLIC_SITE_URL

RUN npm run build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV HOST=0.0.0.0
ENV PORT=4321
ENV NODE_ENV=production

COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./

EXPOSE 4321
CMD ["node", "./dist/server/entry.mjs"]
