FROM debian:bullseye-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Download genai-toolbox binary
ARG VERSION=0.7.0
ARG ARCH=linux/amd64
RUN curl -L -o /usr/local/bin/toolbox \
    https://storage.googleapis.com/genai-toolbox/v${VERSION}/${ARCH}/toolbox \
    && chmod +x /usr/local/bin/toolbox

# Set working directory
WORKDIR /app

# Copy configuration
COPY tools.yaml .

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start the server
CMD ["toolbox", "--tools-file", "tools.yaml", "--host", "0.0.0.0", "--port", "5000"]
