# Multi-stage build for AAES-OS monorepo (Node.js 20)
# Supports: ops-console, platform-api, platform-web

ARG NODE_VERSION=20
ARG SERVICE=platform-api

# Stage 1: Dependencies
FROM node:${NODE_VERSION}-alpine AS deps
WORKDIR /app
RUN apk add --no-cache python3 make g++

# Copy pnpm lock and package manifests
COPY pnpm-lock.yaml .
COPY package.json pnpm-workspace.yaml ./
COPY packages/ packages/
COPY services/ services/

# Install production dependencies only
RUN npm install -g pnpm@10.15.0 && \
    pnpm install --prod

# Stage 2: Build
FROM node:${NODE_VERSION}-alpine AS builder
WORKDIR /app
RUN apk add --no-cache python3 make g++

# Copy everything
COPY . .

# Copy prod dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Install all deps (including dev) for build
RUN npm install -g pnpm@10.15.0 && \
    pnpm install

# Build all packages and services
RUN pnpm -r run build

# Stage 3: Runtime
FROM node:${NODE_VERSION}-alpine AS runtime
WORKDIR /app

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Copy only production dependencies
COPY --from=deps /app/node_modules ./node_modules

# Copy built artifacts
COPY --from=builder /app/packages ./packages
COPY --from=builder /app/services ./services
COPY --from=builder /app/package.json pnpm-workspace.yaml ./

# Service-specific setup happens at runtime via docker-compose or k8s
# The build process compiles all services; runtime selects via entrypoint

# Non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001 && \
    chown -R nodejs:nodejs /app

USER nodejs

# Health check (generic)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

EXPOSE 3000

ENTRYPOINT ["/sbin/dumb-init", "--"]
CMD ["node", "dist/main.js"]
