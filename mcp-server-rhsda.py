#!/usr/bin/env python3
"""Red Hat Security Data API MCP Server

This MCP server provides tools to query Red Hat's Security Data API
for CVE (Common Vulnerabilities and Exposures) and RHSA (Red Hat
Security Advisory) information.

Author: toughIQ <toughiq@gmail.com>
GitHub: https://github.com/toughIQ/rhsda-mcp
License: MIT

API Documentation: https://access.redhat.com/documentation/en-us/red_hat_security_data_api/
"""

import sys
import os
import logging
import re
from typing import Optional, Any
from datetime import datetime

import httpx
from fastmcp import FastMCP

# Initialize FastMCP server
# Host and port configured via FASTMCP_HOST and FASTMCP_PORT environment variables
mcp = FastMCP("rhsda")

# API Configuration
API_BASE_URL = "https://access.redhat.com/hydra/rest/securitydata"
API_TIMEOUT = 30.0
USER_AGENT = "rhsda-mcp-server/1.0"

# Configure logging
# For HTTP: log to stdout (container-visible)
# For stdio: log to stderr (stdout reserved for MCP protocol)
TRANSPORT_MODE = os.getenv("FASTMCP_TRANSPORT", "http")
LOG_LEVEL = os.getenv("FASTMCP_LOG_LEVEL", "INFO")

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr if TRANSPORT_MODE == "stdio" else sys.stdout
)
logger = logging.getLogger(__name__)


# === HELPER FUNCTIONS ===

async def make_api_request(endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Make a request to the Red Hat Security Data API with proper error handling.

    Args:
        endpoint: API endpoint path (e.g., '/cve.json')
        params: Query parameters dictionary

    Returns:
        JSON response data or None if request fails
    """
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Making API request to {endpoint} with params: {params}")
            response = await client.get(url, headers=headers, params=params or {}, timeout=API_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logger.error(f"Request to {endpoint} timed out")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {endpoint}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {endpoint}: {e}")
            return None


def validate_cve_id(cve_id: str) -> bool:
    """Validate CVE ID format (CVE-YYYY-NNNNN).

    Args:
        cve_id: CVE identifier string

    Returns:
        True if valid format, False otherwise
    """
    pattern = r'^CVE-\d{4}-\d{4,}$'
    return bool(re.match(pattern, cve_id.upper()))


def validate_rhsa_id(rhsa_id: str) -> bool:
    """Validate RHSA ID format (RHSA-YYYY:NNNN).

    Args:
        rhsa_id: RHSA identifier string

    Returns:
        True if valid format, False otherwise
    """
    pattern = r'^RHSA-\d{4}:\d{4,}$'
    return bool(re.match(pattern, rhsa_id.upper()))


def validate_severity(severity: str) -> bool:
    """Validate severity level.

    Args:
        severity: Severity level string

    Returns:
        True if valid severity, False otherwise
    """
    valid_severities = ['low', 'moderate', 'important', 'critical']
    return severity.lower() in valid_severities


def format_cve_list(cves: list[dict[str, Any]]) -> str:
    """Format a list of CVEs into a readable markdown table.

    Args:
        cves: List of CVE data dictionaries

    Returns:
        Formatted markdown string
    """
    if not cves:
        return "No CVEs found matching the criteria."

    output = "## CVE Search Results\n\n"
    output += "| CVE ID | Severity | CVSS v3 | CVSS v2 | Public Date | Description |\n"
    output += "|--------|----------|---------|---------|-------------|-------------|\n"

    for cve in cves[:100]:  # Limit to 100 results for readability
        cve_id = cve.get('CVE', 'N/A')
        severity = cve.get('threat_severity', cve.get('ThreatSeverity', 'N/A'))
        cvss3_score = cve.get('cvss3', {}).get('cvss3_base_score', 'N/A') if isinstance(cve.get('cvss3'), dict) else 'N/A'
        cvss_score = cve.get('cvss', {}).get('cvss_base_score', 'N/A') if isinstance(cve.get('cvss'), dict) else 'N/A'
        public_date = cve.get('public_date', cve.get('PublicDate', 'N/A'))

        # Get description from bugzilla or details
        description = 'N/A'
        if 'bugzilla' in cve and isinstance(cve['bugzilla'], dict):
            description = cve['bugzilla'].get('description', 'N/A')
        elif 'details' in cve:
            details_list = cve['details']
            if details_list and len(details_list) > 0:
                description = details_list[0]

        # Truncate long descriptions
        if len(description) > 80:
            description = description[:77] + "..."

        output += f"| {cve_id} | {severity} | {cvss3_score} | {cvss_score} | {public_date} | {description} |\n"

    if len(cves) > 100:
        output += f"\n*Showing first 100 of {len(cves)} results*\n"

    return output


def format_cve_details(cve: dict[str, Any]) -> str:
    """Format detailed CVE information into readable markdown.

    Args:
        cve: CVE data dictionary

    Returns:
        Formatted markdown string
    """
    output = f"# {cve.get('CVE', 'Unknown CVE')}\n\n"

    # Severity and scores
    severity = cve.get('threat_severity', cve.get('ThreatSeverity', 'N/A'))
    output += f"**Threat Severity:** {severity}\n\n"

    # CVSS v3
    if 'cvss3' in cve and isinstance(cve['cvss3'], dict):
        cvss3 = cve['cvss3']
        output += f"**CVSS v3 Score:** {cvss3.get('cvss3_base_score', 'N/A')} "
        output += f"({cvss3.get('cvss3_scoring_vector', 'N/A')})\n"
        output += f"- Status: {cvss3.get('status', 'N/A')}\n\n"

    # CVSS v2
    if 'cvss' in cve and isinstance(cve['cvss'], dict):
        cvss = cve['cvss']
        output += f"**CVSS v2 Score:** {cvss.get('cvss_base_score', 'N/A')} "
        output += f"({cvss.get('cvss_scoring_vector', 'N/A')})\n\n"

    # Publication date
    public_date = cve.get('public_date', cve.get('PublicDate', 'N/A'))
    output += f"**Public Date:** {public_date}\n\n"

    # CWE
    if 'CWE' in cve:
        output += f"**CWE:** {cve['CWE']}\n\n"

    # Description
    output += "## Description\n\n"
    details = cve.get('details', cve.get('Details', []))
    if details:
        for detail in details:
            output += f"{detail}\n\n"

    # Bugzilla info
    if 'bugzilla' in cve and isinstance(cve['bugzilla'], dict):
        bugzilla = cve['bugzilla']
        output += "## Bugzilla\n\n"
        output += f"- **ID:** {bugzilla.get('id', 'N/A')}\n"
        output += f"- **URL:** {bugzilla.get('url', 'N/A')}\n"
        output += f"- **Description:** {bugzilla.get('description', 'N/A')}\n\n"

    # Statement
    if 'statement' in cve or 'Statement' in cve:
        statement = cve.get('statement', cve.get('Statement', ''))
        if statement:
            output += f"## Red Hat Statement\n\n{statement}\n\n"

    # Mitigation
    if 'mitigation' in cve or 'Mitigation' in cve:
        mitigation = cve.get('mitigation', cve.get('Mitigation', ''))
        if mitigation:
            output += f"## Mitigation\n\n{mitigation}\n\n"

    # Affected releases
    if 'affected_release' in cve:
        releases = cve['affected_release']
        if releases:
            output += "## Affected Releases (Fixed)\n\n"
            for release in releases:
                if isinstance(release, dict):
                    product = release.get('product_name', 'N/A')
                    advisory = release.get('advisory', 'N/A')
                    output += f"- **{product}** - Fixed in {advisory}\n"
            output += "\n"

    # Package state
    if 'package_state' in cve:
        states = cve['package_state']
        if states:
            output += "## Package State\n\n"
            for state in states[:10]:  # Limit to first 10
                if isinstance(state, dict):
                    product = state.get('product_name', 'N/A')
                    fix_state = state.get('fix_state', 'N/A')
                    package = state.get('package_name', 'N/A')
                    output += f"- **{product}**: {fix_state} ({package})\n"
            if len(states) > 10:
                output += f"*...and {len(states) - 10} more*\n"
            output += "\n"

    # References
    if 'references' in cve:
        refs = cve['references']
        if refs:
            output += "## References\n\n"
            for ref in refs[:10]:  # Limit to first 10
                output += f"- {ref}\n"
            if len(refs) > 10:
                output += f"*...and {len(refs) - 10} more*\n"
            output += "\n"

    # Acknowledgements
    if 'acknowledgement' in cve or 'Acknowledgements' in cve:
        ack = cve.get('acknowledgement', cve.get('Acknowledgements', ''))
        if ack:
            output += f"## Acknowledgements\n\n{ack}\n\n"

    # Link to Red Hat portal
    cve_id = cve.get('CVE', '')
    if cve_id:
        output += f"**Full details:** https://access.redhat.com/security/cve/{cve_id}\n"

    return output


def format_advisory_list(advisories: list[dict[str, Any]]) -> str:
    """Format a list of security advisories into a readable markdown table.

    Args:
        advisories: List of advisory data dictionaries

    Returns:
        Formatted markdown string
    """
    if not advisories:
        return "No advisories found matching the criteria."

    output = "## Security Advisory Search Results\n\n"
    output += "| RHSA ID | Severity | Release Date | Synopsis | CVEs |\n"
    output += "|---------|----------|--------------|----------|------|\n"

    for adv in advisories[:100]:  # Limit to 100 results
        rhsa_id = adv.get('RHSA', adv.get('name', 'N/A'))
        severity = adv.get('severity', 'N/A')
        release_date = adv.get('release_date', adv.get('initial_release_date', 'N/A'))
        synopsis = adv.get('synopsis', 'N/A')

        # Truncate long synopsis
        if len(synopsis) > 60:
            synopsis = synopsis[:57] + "..."

        # Get CVE list
        cves = adv.get('CVEs', [])
        if isinstance(cves, list) and cves:
            cve_str = ", ".join(cves[:3])
            if len(cves) > 3:
                cve_str += f" +{len(cves) - 3}"
        else:
            cve_str = "N/A"

        output += f"| {rhsa_id} | {severity} | {release_date} | {synopsis} | {cve_str} |\n"

    if len(advisories) > 100:
        output += f"\n*Showing first 100 of {len(advisories)} results*\n"

    return output


def format_advisory_details(advisory: dict[str, Any]) -> str:
    """Format detailed advisory information into readable markdown.

    Args:
        advisory: Advisory data dictionary (CSAF format)

    Returns:
        Formatted markdown string
    """
    # CSAF documents have a complex structure
    doc = advisory.get('document', {})

    # Try to get basic info
    tracking = doc.get('tracking', {})
    rhsa_id = tracking.get('id', 'Unknown Advisory')

    output = f"# {rhsa_id}\n\n"

    # Title/Synopsis
    title = doc.get('title', 'N/A')
    output += f"**Title:** {title}\n\n"

    # Severity from aggregate_severity
    agg_severity = doc.get('aggregate_severity', {})
    severity = agg_severity.get('text', 'N/A')
    output += f"**Severity:** {severity}\n\n"

    # Release date
    initial_release = tracking.get('initial_release_date', 'N/A')
    current_release = tracking.get('current_release_date', 'N/A')
    output += f"**Initial Release:** {initial_release}\n"
    output += f"**Current Release:** {current_release}\n\n"

    # Notes - typically contains description and other details
    notes = doc.get('notes', [])
    for note in notes:
        if isinstance(note, dict):
            note_title = note.get('title', 'Details')
            note_text = note.get('text', '')
            if note_text:
                output += f"## {note_title}\n\n{note_text}\n\n"

    # Vulnerabilities (CVEs addressed)
    vulnerabilities = advisory.get('vulnerabilities', [])
    if vulnerabilities:
        output += "## CVEs Addressed\n\n"
        for vuln in vulnerabilities:
            if isinstance(vuln, dict):
                cve_id = vuln.get('cve', 'N/A')
                scores = vuln.get('scores', [])
                title = vuln.get('title', '')

                output += f"### {cve_id}\n"
                if title:
                    output += f"{title}\n\n"

                # CVSS scores
                for score_data in scores:
                    if isinstance(score_data, dict):
                        cvss = score_data.get('cvss_v3', {})
                        if cvss:
                            base_score = cvss.get('baseScore', 'N/A')
                            vector = cvss.get('vectorString', 'N/A')
                            output += f"- **CVSS v3:** {base_score} ({vector})\n"

                output += "\n"

    # Product tree - shows affected products
    product_tree = advisory.get('product_tree', {})
    branches = product_tree.get('branches', [])
    if branches:
        output += "## Affected Products\n\n"
        # This is a simplified view - CSAF product tree can be very complex
        output += "*Product details available in the full CSAF document*\n\n"

    # References
    references = doc.get('references', [])
    if references:
        output += "## References\n\n"
        for ref in references[:10]:
            if isinstance(ref, dict):
                url = ref.get('url', '')
                summary = ref.get('summary', url)
                output += f"- [{summary}]({url})\n"
        if len(references) > 10:
            output += f"*...and {len(references) - 10} more references*\n"
        output += "\n"

    # Link to Red Hat portal
    if rhsa_id and rhsa_id != 'Unknown Advisory':
        output += f"**Full details:** https://access.redhat.com/errata/{rhsa_id}\n"

    return output


# === MCP TOOLS ===

@mcp.tool()
async def search_cves(
    query: Optional[str] = None,
    severity: Optional[str] = None,
    product: Optional[str] = None,
    package: Optional[str] = None,
    cvss_score: Optional[float] = None,
    cvss3_score: Optional[float] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    per_page: int = 20
) -> str:
    """Search for CVEs in the Red Hat Security Data API.

    Args:
        query: Keyword search (searches CVE IDs, packages, products)
        severity: Filter by severity level (low, moderate, important, critical)
        product: Filter by Red Hat product (e.g., "rhel 8", "openshift")
        package: Filter by affected package name
        cvss_score: Minimum CVSSv2 score threshold (0.0-10.0)
        cvss3_score: Minimum CVSSv3 score threshold (0.0-10.0)
        after: CVEs published after this date (YYYY-MM-DD format)
        before: CVEs published before this date (YYYY-MM-DD format)
        per_page: Number of results per page (default: 20, max: 100)
    """
    # Validate inputs
    if severity and not validate_severity(severity):
        return "❌ Invalid severity. Must be one of: low, moderate, important, critical"

    if cvss_score is not None and (cvss_score < 0.0 or cvss_score > 10.0):
        return "❌ CVSS score must be between 0.0 and 10.0"

    if cvss3_score is not None and (cvss3_score < 0.0 or cvss3_score > 10.0):
        return "❌ CVSS v3 score must be between 0.0 and 10.0"

    # Limit per_page
    per_page = min(per_page, 100)

    # Build API parameters
    params: dict[str, Any] = {
        'per_page': per_page
    }

    if query:
        # Try to determine if query is a CVE ID, package, or product search
        if query.upper().startswith('CVE-'):
            params['ids'] = query.upper()
        elif ' ' in query or any(char.isdigit() for char in query):
            # Likely a product search
            params['product'] = query
        else:
            # Likely a package search
            params['package'] = query

    if severity:
        params['severity'] = severity.lower()

    if product:
        params['product'] = product

    if package:
        params['package'] = package

    if cvss_score is not None:
        params['cvss_score'] = cvss_score

    if cvss3_score is not None:
        params['cvss3_score'] = cvss3_score

    if after:
        params['after'] = after

    if before:
        params['before'] = before

    # Make API request
    data = await make_api_request('/cve.json', params)

    if data is None:
        return "❌ Unable to fetch CVE data. The Red Hat Security Data API may be temporarily unavailable."

    # Format and return results
    cves = data if isinstance(data, list) else []
    return format_cve_list(cves)


@mcp.tool()
async def get_cve_details(cve_id: str) -> str:
    """Get detailed information about a specific CVE.

    Args:
        cve_id: CVE identifier (e.g., "CVE-2024-1234")
    """
    # Validate CVE ID format
    if not validate_cve_id(cve_id):
        return "❌ Invalid CVE ID format. Must be in format: CVE-YYYY-NNNNN"

    cve_id = cve_id.upper()

    # Make API request
    data = await make_api_request(f'/cve/{cve_id}.json')

    if data is None:
        return f"❌ Unable to fetch details for {cve_id}. The CVE may not exist or the API may be temporarily unavailable."

    # Format and return results
    return format_cve_details(data)


@mcp.tool()
async def search_advisories(
    rhsa_ids: Optional[str] = None,
    severity: Optional[str] = None,
    package: Optional[str] = None,
    cve: Optional[str] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    per_page: int = 20
) -> str:
    """Search for Red Hat Security Advisories (RHSA).

    Args:
        rhsa_ids: Comma-separated RHSA IDs (e.g., "RHSA-2024:1234,RHSA-2024:5678")
        severity: Filter by severity level (low, moderate, important, critical)
        package: Filter by affected package name
        cve: Filter by CVE identifier(s) - comma-separated
        after: Advisories published after this date (YYYY-MM-DD format)
        before: Advisories published before this date (YYYY-MM-DD format)
        per_page: Number of results per page (default: 20, max: 100)
    """
    # Validate inputs
    if severity and not validate_severity(severity):
        return "❌ Invalid severity. Must be one of: low, moderate, important, critical"

    # Limit per_page
    per_page = min(per_page, 100)

    # Build API parameters
    params: dict[str, Any] = {
        'per_page': per_page
    }

    if rhsa_ids:
        params['rhsa_ids'] = rhsa_ids

    if severity:
        params['severity'] = severity.lower()

    if package:
        params['package'] = package

    if cve:
        params['cve'] = cve.upper()

    if after:
        params['after'] = after

    if before:
        params['before'] = before

    # Make API request
    data = await make_api_request('/csaf.json', params)

    if data is None:
        return "❌ Unable to fetch advisory data. The Red Hat Security Data API may be temporarily unavailable."

    # Format and return results
    advisories = data if isinstance(data, list) else []
    return format_advisory_list(advisories)


@mcp.tool()
async def get_advisory_details(rhsa_id: str) -> str:
    """Get detailed information about a specific Red Hat Security Advisory.

    Args:
        rhsa_id: RHSA identifier (e.g., "RHSA-2024:1234")
    """
    # Validate RHSA ID format
    if not validate_rhsa_id(rhsa_id):
        return "❌ Invalid RHSA ID format. Must be in format: RHSA-YYYY:NNNN"

    rhsa_id = rhsa_id.upper()

    # Make API request
    data = await make_api_request(f'/csaf/{rhsa_id}.json')

    if data is None:
        return f"❌ Unable to fetch details for {rhsa_id}. The advisory may not exist or the API may be temporarily unavailable."

    # Format and return results
    return format_advisory_details(data)


# === SERVER STARTUP ===

def main():
    """Run the MCP server.

    Server configuration via environment variables:
    - FASTMCP_HOST: Bind address (default: 127.0.0.1, use 0.0.0.0 for containers)
    - FASTMCP_PORT: Server port (default: 8000)
    - FASTMCP_TRANSPORT: Transport protocol (default: http, also supports: stdio, sse)
    - FASTMCP_LOG_LEVEL: Logging level (default: INFO)
    """
    transport = os.getenv("FASTMCP_TRANSPORT", "http")
    logger.info(f"Starting Red Hat Security Data MCP Server ({transport} transport)")
    mcp.run()


if __name__ == "__main__":
    main()
