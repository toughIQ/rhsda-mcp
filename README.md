# 🔐 Red Hat Security Data API MCP Server

A container-native MCP (Model Context Protocol) server that provides tools to query the [Red Hat Security Data API](https://access.redhat.com/documentation/en-us/red_hat_security_data_api/) for CVE (Common Vulnerabilities and Exposures) and RHSA (Red Hat Security Advisory) information.

**👤 Author:** [toughIQ](https://github.com/toughIQ)  
**📜 License:** MIT  
**🔗 Repository:** [https://github.com/toughIQ/rhsda-mcp](https://github.com/toughIQ/rhsda-mcp)

> **⚠️ Community Project Disclaimer**
>
> This is an independent community tool for querying Red Hat's official [Security Data API](https://access.redhat.com/hydra/rest/securitydata). This tool uses Red Hat's official API and [documentation](https://access.redhat.com/documentation/en-us/red_hat_security_data_api/) but is **NOT affiliated with, endorsed by, or supported by Red Hat, Inc.** Use at your own risk.

## ✨ Features

This server exposes four MCP tools:

1. 🔍 **search_cves** - Search for CVEs with flexible filtering options
2. 📋 **get_cve_details** - Get comprehensive details for a specific CVE
3. 📰 **search_advisories** - Search Red Hat Security Advisories (RHSA)
4. 📄 **get_advisory_details** - Get full details for a specific advisory

## 🚀 Quick Start: Container Deployment

**This is a container-native project.** The official and supported deployment method uses Podman (or Docker).

### 📦 Prerequisites

**Recommended:**
- 🐳 **Podman** - Red Hat ecosystem standard ([install guide](https://podman.io/getting-started/installation))

**Alternative:**
- 🐋 **Docker Desktop** ([download](https://www.docker.com/products/docker-desktop/))

### Deploy with Podman Compose

```bash
# Clone the repository
git clone https://github.com/toughIQ/rhsda-mcp.git
cd rhsda-mcp

# Start the server
podman-compose up -d

# Verify it's running
curl http://localhost:6060/
# Should return a connection (HTTP 200 or 404 for root path is OK)

# View logs
podman-compose logs -f
```

**Using Docker Compose instead:**
```bash
docker compose up -d  # Modern Docker Compose (v2)
# or
docker-compose up -d  # Legacy Docker Compose (v1)
```

### Deploy with Podman CLI (No Compose)

```bash
# Build the image
podman build -t rhsda-mcp:latest .

# Run the container
podman run -d \
  --name rhsda-mcp-server \
  -p 6060:6060 \
  --restart unless-stopped \
  rhsda-mcp:latest

# Check health
curl http://localhost:6060/
```

**Using Docker CLI instead:**
```bash
docker build -t rhsda-mcp:latest .
docker run -d --name rhsda-mcp-server -p 6060:6060 rhsda-mcp:latest
```

> 💡 **Note**: This project runs on port **6060** by default to avoid conflicts with other development tools (many use 8000/8080).

## ⚙️ Configuration

### 🖥️ Claude Desktop

Add to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "rhsda": {
      "url": "http://localhost:6060/sse",
      "transport": "sse"
    }
  }
}
```

### 💻 Claude Code CLI

Add to `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "rhsda": {
      "url": "http://localhost:6060/sse",
      "transport": "sse"
    }
  }
}
```

**After adding the configuration**, restart Claude Desktop or Claude Code for the changes to take effect.

## 💡 Usage Examples

Once configured in Claude Code or Claude Desktop, you can use natural language queries:

### 🎯 Example 1: Search for recent critical CVEs

```
Search for critical CVEs in RHEL 9 from the past 30 days
```

This will use the `search_cves` tool with:
- `severity="critical"`
- `product="rhel 9"`
- `after="2026-03-19"` (30 days before today)

### 🎯 Example 2: Get specific CVE details

```
Show me detailed information about CVE-2024-1086
```

This will use the `get_cve_details` tool with:
- `cve_id="CVE-2024-1086"`

### 🎯 Example 3: Search advisories by package

```
Find all security advisories for the kernel package in 2024
```

This will use the `search_advisories` tool with:
- `package="kernel"`
- `after="2024-01-01"`

### 🎯 Example 4: Get advisory details

```
Get the full details of RHSA-2024:0500
```

This will use the `get_advisory_details` tool with:
- `rhsa_id="RHSA-2024:0500"`

### 🎯 Example 5: Complex search with multiple filters

```
Show me important or critical CVEs with CVSS score above 8.0 affecting OpenShift
```

This will use the `search_cves` tool with:
- `severity="important"` or `"critical"` (may require two queries)
- `cvss3_score=8.0`
- `product="openshift"`

## 🛠️ Tool Reference

### search_cves

Search for CVEs with flexible filtering options.

**Parameters:**
- `query` (optional): Keyword search for CVE IDs, packages, or products
- `severity` (optional): Filter by severity - "low", "moderate", "important", "critical"
- `product` (optional): Filter by Red Hat product (e.g., "rhel 8", "openshift")
- `package` (optional): Filter by affected package name
- `cvss_score` (optional): Minimum CVSSv2 score threshold (0.0-10.0)
- `cvss3_score` (optional): Minimum CVSSv3 score threshold (0.0-10.0)
- `after` (optional): CVEs published after date (YYYY-MM-DD format)
- `before` (optional): CVEs published before date (YYYY-MM-DD format)
- `per_page` (optional): Results per page (default: 20, max: 100)

**Returns:** Markdown table with CVE ID, severity, CVSS scores, publication date, and description.

### get_cve_details

Get comprehensive details for a specific CVE.

**Parameters:**
- `cve_id` (required): CVE identifier (e.g., "CVE-2024-1234")

**Returns:** Detailed markdown with threat severity, CVSS scores, description, affected products, mitigation, references, and more.

### search_advisories

Search Red Hat Security Advisories (RHSA).

**Parameters:**
- `rhsa_ids` (optional): Comma-separated RHSA IDs (e.g., "RHSA-2024:1234,RHSA-2024:5678")
- `severity` (optional): Filter by severity - "low", "moderate", "important", "critical"
- `package` (optional): Filter by affected package name
- `cve` (optional): Filter by CVE identifier(s) - comma-separated
- `after` (optional): Advisories published after date (YYYY-MM-DD format)
- `before` (optional): Advisories published before date (YYYY-MM-DD format)
- `per_page` (optional): Results per page (default: 20, max: 100)

**Returns:** Markdown table with RHSA ID, severity, release date, synopsis, and related CVEs.

### get_advisory_details

Get detailed information about a specific Red Hat Security Advisory.

**Parameters:**
- `rhsa_id` (required): RHSA identifier (e.g., "RHSA-2024:1234")

**Returns:** Detailed markdown with advisory title, severity, release dates, description, CVEs addressed, affected products, and references.

## 🐳 Container Operations

### Building the Image

```bash
# Podman
podman build -t rhsda-mcp:latest .

# Docker alternative
docker build -t rhsda-mcp:latest .
```

### Running the Container

```bash
# Podman
podman run -d -p 6060:6060 --name rhsda-mcp-server rhsda-mcp:latest

# Docker alternative
docker run -d -p 6060:6060 --name rhsda-mcp-server rhsda-mcp:latest
```

### Viewing Logs

```bash
# Podman
podman logs rhsda-mcp-server
podman logs -f rhsda-mcp-server  # Follow mode

# Docker alternative
docker logs rhsda-mcp-server
docker logs -f rhsda-mcp-server
```

### Health Checks

The container includes automatic health checks. You can verify the server is responding:

```bash
curl http://localhost:6060/
# Should return HTTP 200 or 404 (root path may not be defined, which is OK)
```

The health check uses the same endpoint and runs every 30 seconds.

### Environment Variables

You can customize the server behavior using environment variables:

- `FASTMCP_TRANSPORT` - Transport mode: `sse` (default) or `stdio`
- `FASTMCP_HOST` - Listen address: `0.0.0.0` (default for containers)
- `FASTMCP_PORT` - Listen port: `6060` (default)
- `PYTHONUNBUFFERED` - Python buffering: `1` (default, ensures logs appear immediately)

Example with custom port:

```bash
podman run -d \
  -p 7070:7070 \
  -e FASTMCP_PORT=7070 \
  --name rhsda-mcp-server \
  rhsda-mcp:latest
```

Or modify `compose.yml`:

```yaml
environment:
  - FASTMCP_PORT=7070
ports:
  - "7070:7070"
```

### Stopping and Removing

```bash
# Podman Compose
podman-compose down

# Podman CLI
podman stop rhsda-mcp-server
podman rm rhsda-mcp-server

# Docker Compose
docker compose down

# Docker CLI
docker stop rhsda-mcp-server
docker rm rhsda-mcp-server
```

### Updating the Image

```bash
# Pull latest changes
git pull

# Rebuild
podman-compose build

# Restart with new image
podman-compose up -d
```

## 🔧 Troubleshooting

### Container Issues

**Container won't start:**

```bash
# Check container logs
podman logs rhsda-mcp-server

# Check container status
podman ps -a | grep rhsda
```

**Health check failing:**

```bash
# Test the endpoint directly
curl -v http://localhost:6060/

# Check if the server is listening
podman exec rhsda-mcp-server curl -f http://localhost:6060/
```

**Port already in use:**

```bash
# Check what's using port 6060
lsof -i :6060
# or
ss -tulpn | grep 6060

# Use a different port mapping
podman run -d -p 7070:6060 --name rhsda-mcp-server rhsda-mcp:latest
# Then update your Claude config URL to http://localhost:7070/sse
```

### Podman-Specific Issues

**Permission denied (Linux):**

If running rootless Podman and encountering permission issues:

```bash
# Ensure your user is in the podman group (if applicable)
sudo usermod -aG podman $USER
newgrp podman
```

**Port binding below 1024:**

Rootless Podman cannot bind to ports below 1024 by default. This project uses port 6060, so this shouldn't be an issue.

**SELinux context errors:**

If you see SELinux denials:

```bash
# Check SELinux status
getenforce

# Temporarily set to permissive for testing
sudo setenforce 0

# If that fixes it, you may need to adjust SELinux contexts
```

### Claude Connection Issues

**Tools not appearing in Claude:**

1. Verify the container is running: `podman ps | grep rhsda`
2. Check health: `curl http://localhost:6060/`
3. Verify URL in config matches: `http://localhost:6060/sse`
4. Restart Claude Desktop/Code after config changes
5. Check Claude logs for MCP server errors

**Connection refused:**

1. Ensure the container is running and healthy
2. Verify the port mapping: `podman port rhsda-mcp-server`
3. Check firewall isn't blocking port 6060
4. Ensure you're using `http://localhost:6060/sse` (not `https://`)

### API Requests Failing

1. Check your internet connection (from inside the container)
2. Verify the Red Hat Security Data API is accessible: visit https://access.redhat.com/hydra/rest/securitydata/cve.json in a browser
3. Check container logs for specific error messages: `podman logs rhsda-mcp-server`

## 🌐 API Information

This server queries the **[Red Hat Security Data API](https://access.redhat.com/hydra/rest/securitydata)**:

- **🔗 Base URL:** [`https://access.redhat.com/hydra/rest/securitydata`](https://access.redhat.com/hydra/rest/securitydata)
- **📚 Documentation:** [Red Hat Security Data API Docs](https://access.redhat.com/documentation/en-us/red_hat_security_data_api/)
- **📊 CVE Endpoint:** [`/cve.json`](https://access.redhat.com/hydra/rest/securitydata/cve.json)
- **📋 RHSA Endpoint:** [`/rhsa.json`](https://access.redhat.com/hydra/rest/securitydata/rhsa.json)
- **💾 Format:** JSON responses
- **🔓 Authentication:** None required (public API)

## 🛡️ Error Handling

The server includes comprehensive error handling:

- **Invalid CVE/RHSA format:** Clear validation messages
- **API failures:** Graceful degradation with informative error messages
- **Network issues:** Timeout handling with 30-second limit
- **Missing data:** Handles incomplete API responses gracefully

## 👨‍💻 Development

### Project Structure

```
rhsda-mcp/
├── mcp-server-rhsda.py      # Main server implementation
├── Dockerfile                # Container image definition
├── compose.yml               # Podman Compose configuration
├── .containerignore          # Build context optimization
├── pyproject.toml            # Project configuration and dependencies
├── README.md                 # This file
└── TESTING.md                # Testing guide
```

### Container-Based Development

For active development with live code changes:

```bash
# Run with volume mount for live code updates
podman run -d \
  -p 6060:6060 \
  -v $(pwd)/mcp-server-rhsda.py:/app/mcp-server-rhsda.py:ro \
  --name rhsda-mcp-dev \
  rhsda-mcp:latest

# Restart container after code changes
podman restart rhsda-mcp-dev
```

### Adding Features

The server is designed to be extensible. To add new tools:

1. Add a new function decorated with `@mcp.tool()` in `mcp-server-rhsda.py`
2. Implement the API request logic using `make_api_request()`
3. Format the response using a new formatter function
4. Rebuild the container: `podman build -t rhsda-mcp:latest .`
5. Update this README with the new tool documentation

### Logging

The server uses transport-aware logging:

- **SSE mode (default):** Logs to stdout (visible in container logs)
- **stdio mode:** Logs to stderr (required for stdio protocol)

View logs:
```bash
podman logs -f rhsda-mcp-server
```

## 🤝 Contributing

Contributions are welcome! Please ensure:

1. Code follows the existing style
2. All tools include proper docstrings
3. Error handling is comprehensive
4. README is updated for new features
5. Container builds successfully
6. All MCP tools function correctly

To contribute:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 👤 Author & Maintainer

**toughIQ**
- 🐙 GitHub: [@toughIQ](https://github.com/toughIQ)
- 📧 Email: toughiq@gmail.com

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

This is an independent community project not affiliated with, endorsed by, or supported by Red Hat, Inc. The Red Hat Security Data API is provided by Red Hat under their own terms of service.

## 📚 Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Red Hat Security Data API Documentation](https://access.redhat.com/documentation/en-us/red_hat_security_data_api/)
- [Red Hat Customer Portal](https://access.redhat.com/)
- [CVE Database](https://www.cve.org/)
- [Podman Documentation](https://docs.podman.io/)
- [Fedora Container Images on Quay.io](https://quay.io/organization/fedora)

---

## 📎 Appendix: Local Installation (Unsupported)

> ⚠️ **WARNING: This installation method is unsupported.**
>
> The project is developed and tested as a containerized application. Local installation is provided for advanced users only. We do not maintain or troubleshoot local installations.

### When You Might Use This

- Active development/debugging of the server code itself
- Air-gapped environments without container support
- Educational/learning purposes

### Requirements

- Python 3.12 or higher
- pip or [uv](https://github.com/astral-sh/uv)

### Option A: Using pip

```bash
# Clone the repository
git clone https://github.com/toughIQ/rhsda-mcp.git
cd rhsda-mcp

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install httpx mcp

# Test the server (stdio mode)
FASTMCP_TRANSPORT=stdio python mcp-server-rhsda.py
# Press Ctrl+C to exit
```

### Option B: Using uv

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <repo-url> rhsda-mcp
cd rhsda-mcp

# Install dependencies
uv sync

# Test the server (stdio mode)
FASTMCP_TRANSPORT=stdio uv run mcp-server-rhsda.py
```

### stdio Configuration

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "rhsda": {
      "command": "/absolute/path/to/rhsda-mcp/.venv/bin/python",
      "args": [
        "mcp-server-rhsda.py"
      ],
      "cwd": "/absolute/path/to/rhsda-mcp",
      "env": {
        "FASTMCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

**Claude Code** (`~/.claude/mcp.json`):

```json
{
  "mcpServers": {
    "rhsda": {
      "command": "/absolute/path/to/rhsda-mcp/.venv/bin/python",
      "args": [
        "mcp-server-rhsda.py"
      ],
      "cwd": "/absolute/path/to/rhsda-mcp",
      "env": {
        "FASTMCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

**Important:** Replace `/absolute/path/to/rhsda-mcp` with your actual installation directory.

### Note

For production or regular use, please use the containerized deployment method described at the top of this document.
