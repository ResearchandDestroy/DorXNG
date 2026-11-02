#!/usr/bin/env python3
# DorXNG MCP Server -- Drive DorXNG from AI Agents over the Model Context Protocol
#
# stdio (default):        python3 mcp_server.py
# Streamable HTTP:        python3 mcp_server.py --http [--host 127.0.0.1] [--port 8765]
#
# Environment: DORXNG_SERVER (comma separated list), DORXNG_DB_DIR, DORXNG_DELAY, DORXNG_MAX_JOBS
# Please DO NOT point DorXNG at public SearXNG instances.
import argparse
import atexit
import functools
import os
import re
import sqlite3
import sys

import requests
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp_types import ToolAnnotations

import dorxng_core as core

HERE = os.path.dirname(os.path.abspath(__file__))
LISTS = {'ghdb': os.path.join(HERE, 'query.lst'), 'operators': os.path.join(HERE, 'operators.lst')}
MAX_SEARCH_PAGES = 10

INSTRUCTIONS = """DorXNG harvests OSINT data with advanced search operators (Google dorks) through a
self-hosted SearXNG instance that routes every query over Tor by default.

Workflow: check `server_status` first. Use `search` for a quick look (a few pages), and
`start_harvest` + `job_status` for deep runs (many pages, query lists, loops). Every result is
stored in a SQLite database (default dorxng.db) that `query_database` and `database_stats` read.
`list_dorks` pages through the bundled GHDB dork list and the operator test list.

Reliable operators: site:, -site:, filetype:/ext:, intitle:, "exact phrase". inurl: is treated as a
ranking hint by every engine, so expect some noise. Only set no_tor=true when the user explicitly
wants it: it exposes the SearXNG host's IP address to the search providers."""

mcp = MCPServer('DorXNG', instructions=INSTRUCTIONS, version='2.0.0')
jobs = core.JobManager()
atexit.register(jobs.stop_all)

READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
SEARCHES = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False,
                           open_world_hint=True)


def expected_errors(fn):
    """Report expected failures (bad arguments, missing databases, unreachable servers) to the agent."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (ValueError, KeyError, FileNotFoundError, RuntimeError, re.error, sqlite3.Error,
                requests.exceptions.RequestException) as error:
            message = error.args[0] if isinstance(error, KeyError) and error.args else error
            raise ToolError(str(message)) from error
    return wrapper


def _servers(server):
    return [s.strip() for s in server.split(',') if s.strip()] if server else core.servers_from_env()


def _engines(no_tor, servers):
    return core.direct_engines(servers) if no_tor else None


@mcp.tool(annotations=READ_ONLY)
@expected_errors
def server_status(server: str | None = None) -> dict:
    """Check that the DorXNG SearXNG server(s) are reachable and list their Tor, direct (--no-tor) and
    onion engines. `server` defaults to DORXNG_SERVER; pass a comma separated list for several."""
    return {'servers': [core.server_status(s) for s in _servers(server)]}


@mcp.tool(annotations=SEARCHES)
@expected_errors
def search(query: str, pages: int = 1, concurrent: int = 4, no_tor: bool = False,
           database: str = 'dorxng.db', server: str | None = None) -> dict:
    """Run a dork query for pages 1..`pages` (max 10 per call), store every result in `database` and
    return the results that were not already in it, plus engine errors.

    query: any SearXNG query, e.g. 'site:example.com filetype:pdf' or '!ah onion services'.
    no_tor: query providers directly instead of over Tor. Exposes the SearXNG host's IP address.
    For more pages, query lists or loops use start_harvest."""
    pages = max(1, min(pages, MAX_SEARCH_PAGES))
    servers = _servers(server)
    totals = core.search_pages(servers, query, pages, concurrent, _engines(no_tor, servers), delay=0,
                               database=database, no_new_results=0)
    return {
        'query': query, 'mode': 'direct (no Tor)' if no_tor else 'Tor', 'database': database,
        'pages': totals['pages'], 'results_returned': totals['results'], 'new_results': len(totals['new']),
        'results': totals['new'], 'unresponsive_engines': totals['unresponsive_engines'],
        'errors': totals['errors'],
    }


@mcp.tool(annotations=SEARCHES)
@expected_errors
def start_harvest(queries: list[str] | None = None, dork_list: str | None = None, pages: int = 64,
                  concurrent: int = 4, loops: int = 1, no_new_results: int = 4, no_tor: bool = False,
                  database: str = 'dorxng.db', server: str | None = None, delay: float | None = None) -> dict:
    """Start a background harvest (like `DorXNG.py -Q list -c4 -n64 -L1`) and return a job_id at once.

    queries: dork queries to run, or dork_list: 'ghdb' (every GHDB dork, ~8k) / 'operators'.
    pages: pages per query. loops: passes over all queries (0 = run until stopped).
    no_new_results: move to the next query after this many batches without new URLs (0 = never).
    delay: seconds between batches (default DORXNG_DELAY, 4). no_tor exposes the SearXNG host's IP.
    Poll with job_status, stop with stop_job. Results land in `database` as they arrive."""
    if dork_list:
        if dork_list not in LISTS:
            raise ValueError('dork_list must be one of: ' + ', '.join(LISTS))
        queries = (queries or []) + core.read_list(LISTS[dork_list])
    if not queries:
        raise ValueError('pass queries and/or dork_list')
    core.db_path(database)  # validate the name before starting
    servers = _servers(server)
    job = jobs.start(queries=queries, pages=max(1, pages), concurrent=max(1, concurrent), loops=max(0, loops),
                     no_new_results=max(0, no_new_results), engines=_engines(no_tor, servers),
                     servers=servers, database=database, delay=delay)
    return job.status()


@mcp.tool(annotations=READ_ONLY)
@expected_errors
def job_status(job_id: str) -> dict:
    """Progress of a harvest job: state, current query and pages, counts and the 20 newest results."""
    return jobs.get(job_id).status()


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True,
                                      open_world_hint=False))
@expected_errors
def stop_job(job_id: str) -> dict:
    """Stop a running harvest job. Results gathered so far stay in its database."""
    return jobs.stop(job_id).status()


@mcp.tool(annotations=READ_ONLY)
@expected_errors
def list_jobs() -> dict:
    """All harvest jobs started by this server, newest first."""
    ordered = sorted(jobs.jobs.values(), key=lambda j: j.started, reverse=True)
    return {'jobs': [{k: v for k, v in j.status().items() if k != 'recent_new_results'} for j in ordered]}


@mcp.tool(annotations=READ_ONLY)
@expected_errors
def query_database(pattern: str, database: str = 'dorxng.db', limit: int = 200) -> dict:
    """Regex search (case insensitive) over result titles and URLs, like `DorXNG.py -D`.
    Example patterns: '\\.sql$', 'admin|login', '^https?://[^/]*\\.gov/'."""
    return core.query_database(database, pattern, max(1, min(limit, 2000)))


@mcp.tool(annotations=READ_ONLY)
@expected_errors
def database_stats(database: str = 'dorxng.db') -> dict:
    """Row counts, results per query and the most common domains in a database."""
    return core.database_stats(database)


@mcp.tool(annotations=READ_ONLY)
@expected_errors
def list_databases() -> dict:
    """DorXNG databases (*.db) in DORXNG_DB_DIR with their row counts."""
    return core.list_databases()


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True,
                                      open_world_hint=False))
@expected_errors
def merge_databases(source: str, target: str) -> dict:
    """Merge every row of `source` into `target` (created if missing), like `DorXNG.py -d target -m source`."""
    return core.merge_databases(source, target)


@mcp.tool(annotations=READ_ONLY)
@expected_errors
def list_dorks(source: str = 'ghdb', filter: str | None = None, limit: int = 50, offset: int = 0) -> dict:
    """Page through bundled dork lists. source: 'ghdb' (Google Hacking Database, ~8k dorks) or
    'operators' (one query per advanced search operator). filter: optional case insensitive regex."""
    if source not in LISTS:
        raise ValueError('source must be one of: ' + ', '.join(LISTS))
    dorks = core.read_list(LISTS[source])
    if filter:
        regex = re.compile(filter, re.IGNORECASE)
        dorks = [d for d in dorks if regex.search(d)]
    limit = max(1, min(limit, 500))
    return {'source': source, 'total': len(dorks), 'offset': offset, 'dorks': dorks[offset:offset + limit]}


@mcp.resource('dorxng://operators', mime_type='text/plain')
def operators_list() -> str:
    """operators.lst: one query per advanced search operator, used to validate the enabled engines."""
    with open(LISTS['operators'], encoding='utf-8') as f:
        return f.read()


@mcp.resource('dorxng://readme', mime_type='text/markdown')
def readme() -> str:
    """The DorXNG README: setup, engines, operators, CLI options and tips."""
    with open(os.path.join(HERE, 'README.md'), encoding='utf-8') as f:
        return f.read()


@mcp.prompt()
def dork_recon(target_domain: str) -> str:
    """Guided OSINT reconnaissance of one domain with DorXNG."""
    return f"""Run passive OSINT reconnaissance on {target_domain} with the DorXNG tools.

1. Call server_status and confirm the server is reachable.
2. Use a database named after the target, e.g. "{target_domain.replace('.', '_')}.db".
3. Run `search` with a handful of focused dorks, for example:
   site:{target_domain} filetype:pdf | site:{target_domain} (filetype:xls OR filetype:xlsx OR filetype:csv)
   site:{target_domain} intitle:"index of" | site:{target_domain} inurl:login | site:{target_domain} -site:www.{target_domain}
   site:{target_domain} (filetype:sql OR filetype:env OR filetype:log OR filetype:bak)
4. For anything promising, start_harvest with more pages and poll job_status.
5. Summarize with database_stats and query_database: subdomains seen, exposed documents and file
   types, directory listings, login portals. Report URLs exactly as stored; do not visit them.
Only use no_tor if I ask for it."""


def main():
    parser = argparse.ArgumentParser(description='DorXNG MCP server')
    parser.add_argument('--http', action='store_true', help='Serve Streamable HTTP instead of stdio')
    parser.add_argument('--host', default='127.0.0.1', help='HTTP bind address (default 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8765, help='HTTP port (default 8765)')
    args = parser.parse_args()

    if args.http:
        if args.host not in ('127.0.0.1', 'localhost', '::1'):
            print(f'WARNING: serving DorXNG MCP on {args.host}; anyone who can reach it can run searches.',
                  file=sys.stderr)
        mcp.run('streamable-http', host=args.host, port=args.port)
    else:
        mcp.run('stdio')


if __name__ == '__main__':
    main()
