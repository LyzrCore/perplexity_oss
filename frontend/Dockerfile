FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat git
WORKDIR /app

COPY package.json ./
COPY lyzr-agent-local ./lyzr-agent-local
# Build the local lyzr-agent package first
RUN cd lyzr-agent-local && npm install --ignore-scripts && npm run build
# Install main project dependencies
RUN npm install

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/lyzr-agent-local ./lyzr-agent-local
COPY . .

# Build arguments for environment variables
# Default to /api if not provided, will be overridden at runtime
# ARG NEXT_PUBLIC_API_URL=/api
ARG NEXT_PUBLIC_PRO_MODE_ENABLED=true

ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_PRO_MODE_ENABLED=${NEXT_PUBLIC_PRO_MODE_ENABLED}

RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000 3003

ENV PORT=3000

# server.js is created by next build from the standalone output
CMD ["node", "server.js"]
