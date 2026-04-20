# Use Fedora minimal image for smaller footprint (~136 MB base vs ~1.08 GB)
FROM quay.io/fedora/fedora-minimal:latest

WORKDIR /app

# Install Python 3.12 and curl (for health checks)
RUN microdnf install -y python3.12 curl && \
    microdnf clean all

# Bootstrap pip for python3.12 and install dependencies
COPY pyproject.toml ./
RUN python3.12 -m ensurepip --upgrade && \
    python3.12 -m pip install --no-cache-dir httpx>=0.28.1 'fastmcp>=0.3.0'

# Copy server code
COPY mcp-server-rhsda.py ./

# Create non-root user for security
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app
USER mcpuser

# Expose port 8000 (FastMCP default)
EXPOSE 8000

# Environment variables for FastMCP
ENV FASTMCP_HOST=0.0.0.0 \
    FASTMCP_PORT=8000 \
    FASTMCP_LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1

# Run server
CMD ["python3.12", "mcp-server-rhsda.py"]
