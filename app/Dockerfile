# Build stage
FROM golang:1.21-alpine AS builder

# Install dependencies required for build
RUN apk add --no-cache git ca-certificates build-base

# Set working directory
WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo \
    -ldflags '-w -extldflags "-static"' \
    -o main ./cmd/server

# Final stage
FROM alpine:latest

# Install CA certificates and curl for healthchecks
RUN apk --no-cache add ca-certificates curl

# Create app user
RUN addgroup -S app && adduser -S app -G app

# Set working directory
WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/main .
COPY --from=builder /app/config ./config

# Create logs directory
RUN mkdir -p /app/logs && chown -R app:app /app

# Change ownership to app user
RUN chown -R app:app /app

# Switch to app user
USER app

# Expose ports
EXPOSE 8080 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["./main"]