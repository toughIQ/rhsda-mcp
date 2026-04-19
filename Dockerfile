# Use Fedora-based Python image (Red Hat ecosystem alignment)
FROM quay.io/fedora/python-312:latest

# Switch to root to install system packages
USER 0

WORKDIR /app

# Install curl for health checks
RUN dnf install -y curl && \
    dnf clean all

# Copy and install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir httpx>=0.28.1 mcp>=1.2.0

# Copy server code
COPY mcp-server-rhsda.py ./

# Create non-root user for security
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app
USER mcpuser

# Expose port 8000 (FastMCP default)
EXPOSE 8000

# Environment variables
ENV FASTMCP_TRANSPORT=sse \
    PYTHONUNBUFFERED=1

# Run server
CMD ["python", "mcp-server-rhsda.py"]
