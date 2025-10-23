# Production Dockerfile for Frontend
# Multi-stage build for optimized production image

# Build stage
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Install system dependencies including git for the local lyzr-agent package
RUN apk add --no-cache libc6-compat git

# Copy package files
COPY package.json ./

# Copy the local lyzr-agent package
COPY lyzr-agent-local ./lyzr-agent-local

# Build the local lyzr-agent package first
RUN cd lyzr-agent-local && npm install && npm run build

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Set build-time environment variables with defaults
ARG NEXT_PUBLIC_API_URL=/api
ARG NEXT_PUBLIC_PRO_MODE_ENABLED=true

ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_PRO_MODE_ENABLED=${NEXT_PUBLIC_PRO_MODE_ENABLED}

# Build the Next.js application
RUN npm run build

# Production stage
FROM node:18-alpine AS runner

# Set working directory
WORKDIR /app

# Set environment to production
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application from builder stage
COPY --from=builder /app/public ./public

# Set permissions for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Copy build artifacts
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

# Expose port
EXPOSE 3000

# Start the application
CMD ["node", "server.js"]