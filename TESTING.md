# Testing Guide for Red Hat Security Data MCP Server

*Documentation created with assistance from [Claude Code](https://claude.ai/code).*

## Quick Verification

### 1. Container-Based Testing (Official Method)

#### Build and Start with Podman

```bash
# Start the server
podman-compose up -d

# Verify it's running
curl -X POST http://localhost:6060/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
# Should return a JSON-RPC response with server info

# Check health status
podman ps | grep rhsda

# View logs
podman-compose logs
```

**Using Docker instead:**
```bash
docker compose up -d
curl -X POST http://localhost:6060/mcp -H "Content-Type: application/json" -d '{}'
docker compose logs
```

### 2. Configure Claude

Register the server with Claude Code:

```bash
claude mcp add --transport http -s project rhsda http://localhost:6060/mcp
```

Or add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "rhsda": {
      "type": "http",
      "url": "http://localhost:6060/mcp"
    }
  }
}
```

Restart Claude Code.

### 3. Check Tool Availability

Once configured in Claude Code/Desktop, verify all four tools are available:
- ✅ search_cves
- ✅ get_cve_details
- ✅ search_advisories
- ✅ get_advisory_details

## Test Queries

### Test 1: Search for Critical CVEs

**Query:**
```
Search for critical CVEs in RHEL 9 from the past 30 days
```

**Expected Tool Call:**
```
search_cves(
    severity="critical",
    product="rhel 9",
    after="<30-days-ago>"
)
```

**Expected Result:**
- Markdown table with CVE IDs, severities, CVSS scores
- At least a few results (if any critical CVEs exist in that timeframe)
- No error messages

### Test 2: Get CVE Details

**Query:**
```
Show me details for CVE-2024-1086
```

**Expected Tool Call:**
```
get_cve_details(cve_id="CVE-2024-1086")
```

**Expected Result:**
- Detailed markdown with:
  - Threat severity rating
  - CVSS scores (v2 and/or v3)
  - Description
  - Affected products
  - Mitigation information
  - References

### Test 3: Search Advisories

**Query:**
```
Find all security advisories for the kernel package in 2024
```

**Expected Tool Call:**
```
search_advisories(
    package="kernel",
    after="2024-01-01"
)
```

**Expected Result:**
- Markdown table with RHSA IDs, severities, dates
- Multiple results (kernel advisories are common)
- Related CVEs listed

### Test 4: Get Advisory Details

**Query:**
```
Get the full details of RHSA-2024:0500
```

**Expected Tool Call:**
```
get_advisory_details(rhsa_id="RHSA-2024:0500")
```

**Expected Result:**
- Advisory title and description
- Severity rating
- Release dates
- CVEs addressed
- Affected products
- References and links

### Test 5: Complex Query

**Query:**
```
Show me important CVEs with CVSS score above 8.0 affecting OpenShift from the last 90 days
```

**Expected Tool Call:**
```
search_cves(
    severity="important",
    cvss3_score=8.0,
    product="openshift",
    after="<90-days-ago>"
)
```

**Expected Result:**
- Filtered results matching all criteria
- High-severity CVEs only
- OpenShift-specific vulnerabilities

## Error Handling Tests

### Test Invalid CVE ID

**Query:**
```
Get details for CVE-INVALID-123
```

**Expected Result:**
- Error message about invalid CVE format
- No API call made

### Test Non-Existent CVE

**Query:**
```
Get details for CVE-9999-99999
```

**Expected Result:**
- Error message that CVE doesn't exist or API unavailable
- Graceful error handling

### Test Non-Existent Advisory

**Query:**
```
Get details for RHSA-9999:9999
```

**Expected Result:**
- Error message that advisory doesn't exist
- No crash or unhandled exception

## Performance Tests

### Response Time

All queries should return within reasonable time:
- Simple queries: < 5 seconds
- Complex queries: < 15 seconds
- Detail lookups: < 10 seconds

If responses are slower, check:
1. Internet connection speed
2. Red Hat API availability
3. Container resource limits

### Concurrent Requests

The server should handle multiple concurrent requests from Claude:

**Test:**
Ask Claude to perform multiple queries in succession without waiting for each to complete.

**Expected:**
- All queries complete successfully
- No timeouts or crashes
- Results returned in reasonable time

## Container-Specific Tests

### Health Check

```bash
# Container should be healthy
podman ps

# Health check endpoint should respond
curl -X POST http://localhost:6060/mcp -H "Content-Type: application/json" -d '{}'
```

### Log Inspection

```bash
# Check for startup message
podman logs rhsda-mcp-server | grep "Starting Red Hat Security Data MCP Server"

# Check for dual transport startup
podman logs rhsda-mcp-server | grep "dual SSE + HTTP transport"

# Should see log messages for API requests
podman logs rhsda-mcp-server | grep "Making API request"
```

### Port Verification

```bash
# Verify port 6060 is listening
ss -tulpn | grep 6060
# or
lsof -i :6060
```

### Restart Resilience

```bash
# Restart container
podman restart rhsda-mcp-server

# Wait for startup
sleep 5

# Verify still working
curl -X POST http://localhost:6060/mcp -H "Content-Type: application/json" -d '{}'

# Test a query in Claude
```

## Development Testing (Local - Unsupported)

> **Note:** Local testing is unsupported. Use containers for official testing.

For active development only:

```bash
# Test HTTP mode locally (starts dual SSE + HTTP transport)
FASTMCP_HOST=127.0.0.1 FASTMCP_PORT=6060 python mcp-server-rhsda.py &

# Wait for startup
sleep 2

# Test endpoint
curl -X POST http://localhost:6060/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'

# Kill when done
pkill -f mcp-server-rhsda.py
```

```bash
# Test stdio mode locally
FASTMCP_TRANSPORT=stdio python mcp-server-rhsda.py
# Should see: "Starting Red Hat Security Data MCP Server (stdio transport)"
# Press Ctrl+C to exit
```

## Troubleshooting Test Failures

### Tools Not Appearing in Claude

1. Check container is running: `podman ps | grep rhsda`
2. Check logs for errors: `podman logs rhsda-mcp-server`
3. Verify config URL: `http://localhost:6060/mcp`
4. Restart Claude after config changes
5. For Claude Code: check server status with `/mcp` command or `claude mcp list`

### API Calls Failing

1. Check internet connectivity
2. Visit https://access.redhat.com/hydra/rest/securitydata/cve.json in browser
3. Check container logs for specific errors
4. Verify Red Hat API is not rate-limiting

### Performance Issues

1. Check container resources: `podman stats rhsda-mcp-server`
2. Check network latency to Red Hat API
3. Review API timeout settings (default: 30 seconds)

## Cleanup After Testing

```bash
# Stop and remove container
podman-compose down

# Or with Podman CLI
podman stop rhsda-mcp-server
podman rm rhsda-mcp-server

# Remove image (optional)
podman rmi rhsda-mcp:latest
```
