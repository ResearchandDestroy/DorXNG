# DorXNG Core -- CLI Free Search, Database and Harvest Functions
# Used by the DorXNG MCP Server (mcp_server.py). Databases are Fully
# Compatible with the DorXNG CLI (-d, -D, -m).
import itertools
import os
import re
import sqlite3
import threading
import time
import urllib.parse
import uuid
from collections import Counter, deque
from concurrent.futures import ThreadPoolExecutor

import requests

requests.packages.urllib3.disable_warnings()

HEADERS = {'User-Agent': 'DorXNG'}
REQUEST_TIMEOUT = 120


# Configuration From Environment Variables
def servers_from_env():
    raw = os.environ.get('DORXNG_SERVER', 'https://172.17.0.2/search')
    return [s.strip() for s in raw.split(',') if s.strip()]


def db_dir():
    return os.path.abspath(os.environ.get('DORXNG_DB_DIR', os.getcwd()))


def default_delay():
    return float(os.environ.get('DORXNG_DELAY', '4'))


def max_jobs():
    return int(os.environ.get('DORXNG_MAX_JOBS', '4'))


# SearXNG Requests
def search_page(server, query, pageno=1, engines=None):
    """Issue one SearXNG JSON query. Never raises; errors are returned in 'error'."""
    params = {'q': query, 'format': 'json', 'pageno': pageno}
    if engines:
        params['engines'] = engines
    try:
        response = requests.post(server, params, headers=HEADERS, verify=False, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    # requests' JSONDecodeError is also a RequestException: catch it first so a non-JSON page
    # counts as an empty batch (like the CLI) instead of being resent
    except ValueError:
        return {'results': [], 'unresponsive_engines': [], 'error': 'invalid JSON response', 'retry': False}
    except requests.exceptions.RequestException as error:
        return {'results': [], 'unresponsive_engines': [], 'error': str(error), 'retry': True}
    results = [{'title': r.get('title') or '', 'url': r.get('url') or '', 'engines': r.get('engines', [])}
               for r in data.get('results', []) if r.get('url')]
    return {'results': results, 'unresponsive_engines': data.get('unresponsive_engines', []), 'error': None,
            'retry': False}


def config_url(server):
    return urllib.parse.urljoin(server, 'config')


def fetch_config(server):
    response = requests.get(config_url(server), headers=HEADERS, verify=False, timeout=30)
    response.raise_for_status()
    return response.json()


def direct_engines(servers):
    """Direct (no Tor) engines shared by every server, as the SearXNG 'engines' parameter."""
    shared = None
    for server in servers:
        names = {e['name'] for e in fetch_config(server).get('engines', []) if e['name'].endswith(' direct')}
        shared = names if shared is None else shared & names
    if not shared:
        raise RuntimeError('no direct (no Tor) engines configured on: ' + ', '.join(servers))
    return ','.join(sorted(shared))


def server_status(server):
    started = time.time()
    try:
        config = fetch_config(server)
    except (requests.exceptions.RequestException, ValueError) as error:
        return {'server': server, 'reachable': False, 'error': str(error)}
    engines = config.get('engines', [])
    return {
        'server': server,
        'reachable': True,
        'latency_seconds': round(time.time() - started, 2),
        'version': config.get('version'),
        'tor_engines': sorted(e['name'] for e in engines
                              if e.get('enabled') and 'general' in e.get('categories', [])),
        'direct_engines': sorted(e['name'] for e in engines if e['name'].endswith(' direct')),
        'onion_engines': sorted(e['name'] for e in engines if 'onions' in e.get('categories', [])),
    }


# Databases (Same Schema as the DorXNG CLI)
_db_locks = {}
_db_locks_guard = threading.Lock()


def db_path(name):
    """Resolve a database name inside DORXNG_DB_DIR; refuse paths outside it."""
    if not name or os.path.basename(name) != name or not name.endswith('.db'):
        raise ValueError('database must be a plain file name ending in .db (e.g. "dorxng.db")')
    return os.path.join(db_dir(), name)


def _lock(path):
    with _db_locks_guard:
        return _db_locks.setdefault(path, threading.Lock())


def _connect(path):
    connection = sqlite3.connect(path, timeout=30)
    connection.execute('CREATE TABLE IF NOT EXISTS search_results (query TEXT, title TEXT, url TEXT)')
    return connection


def store_results(database, query, results):
    """Insert results, skipping exact duplicate rows. Returns results whose URL was not yet in the database."""
    path = db_path(database)
    with _lock(path):
        connection = _connect(path)
        try:
            known = {row[0] for row in connection.execute(
                'SELECT url FROM search_results WHERE url IN (%s)' % ','.join('?' * len(results)),
                [r['url'] for r in results]).fetchall()} if results else set()
            new, seen = [], set()
            for r in results:
                exists = connection.execute('SELECT 1 FROM search_results WHERE query=? AND title=? AND url=?',
                                            (query, r['title'], r['url'])).fetchone()
                if not exists:
                    connection.execute('INSERT INTO search_results VALUES (?, ?, ?)', (query, r['title'], r['url']))
                if r['url'] not in known and r['url'] not in seen:
                    new.append(r)
                    seen.add(r['url'])
            connection.commit()
        finally:
            connection.close()
    return new


def query_database(database, pattern, limit=200):
    path = db_path(database)
    if not os.path.exists(path):
        raise FileNotFoundError(f'no database "{database}" in {db_dir()}')
    regex = re.compile(pattern, re.IGNORECASE)
    connection = _connect(path)
    try:
        rows = connection.execute('SELECT query, title, url FROM search_results').fetchall()
    finally:
        connection.close()
    matches = [{'query': q, 'title': t, 'url': u} for q, t, u in rows
               if regex.search(t or '') or regex.search(u or '')]
    return {'database': database, 'total_matches': len(matches), 'results': matches[:limit]}


def database_stats(database, top=20):
    path = db_path(database)
    if not os.path.exists(path):
        raise FileNotFoundError(f'no database "{database}" in {db_dir()}')
    connection = _connect(path)
    try:
        rows = connection.execute('SELECT query, url FROM search_results').fetchall()
    finally:
        connection.close()
    hosts = Counter((urllib.parse.urlparse(u).hostname or '') for _, u in rows)
    return {
        'database': database,
        'rows': len(rows),
        'unique_urls': len({u for _, u in rows}),
        'queries': [{'query': q, 'rows': n} for q, n in Counter(q for q, _ in rows).most_common()],
        'top_domains': [{'domain': h, 'rows': n} for h, n in hosts.most_common(top)],
    }


def list_databases():
    out = []
    for name in sorted(os.listdir(db_dir())):
        if name.endswith('.db'):
            try:
                connection = sqlite3.connect(os.path.join(db_dir(), name))
                rows = connection.execute('SELECT count(*) FROM search_results').fetchone()[0]
                connection.close()
            except sqlite3.Error:
                continue
            out.append({'database': name, 'rows': rows})
    return {'db_dir': db_dir(), 'databases': out}


def merge_databases(source, target):
    src = db_path(source)
    if not os.path.exists(src):
        raise FileNotFoundError(f'no database "{source}" in {db_dir()}')
    connection = sqlite3.connect(src)
    try:
        rows = connection.execute('SELECT query, title, url FROM search_results').fetchall()
    finally:
        connection.close()
    added = 0
    path = db_path(target)
    with _lock(path):
        connection = _connect(path)
        try:
            for row in rows:
                if not connection.execute('SELECT 1 FROM search_results WHERE query=? AND title=? AND url=?',
                                          row).fetchone():
                    connection.execute('INSERT INTO search_results VALUES (?, ?, ?)', row)
                    added += 1
            connection.commit()
            total = connection.execute('SELECT count(*) FROM search_results').fetchone()[0]
        finally:
            connection.close()
    return {'source': source, 'target': target, 'rows_added': added, 'target_rows': total}


# Dork Lists
def read_list(path):
    with open(path, encoding='utf-8', errors='replace') as f:
        return [line.rstrip('\n') for line in f if line.strip()]


# No New Results Counter (Same Rules as the DorXNG CLI -r/--nonewresults)
def empty_batch_attempts(no_new_results, pages):
    """Empty batches allowed before moving on: 0 disables, the default 4 means 3 attempts,
    any other N means N attempts. Like the CLI, only active when iterating pages (pages > 1)."""
    if not no_new_results or pages <= 1:
        return 0
    return 3 if no_new_results == 4 else no_new_results


# Paging Engine
def search_pages(servers, query, pages, concurrent=4, engines=None, delay=None, database='dorxng.db',
                 no_new_results=4, stop_event=None, on_batch=None, count_first_batch=True, retries=None,
                 full_batches=False, on_retry=None):
    """Search pages 1..pages in concurrent batches, rotating servers per batch.

    Like the CLI, a batch that returns no results at all counts against `no_new_results`
    (see empty_batch_attempts); batches with results do not reset the count. The CLI never
    counts the first batch of a loop pass, so harvests pass count_first_batch=False for it.

    Also like the CLI, a batch with an HTTP/connection error is resent on the next server after
    a pause (`delay`, at least 1 second); `retries` caps the resends (None = until stopped).
    full_batches: always request `concurrent` pages per batch, like the CLI (-n10 -c4 requests
    pages 1-12); otherwise stop exactly at `pages`.
    on_batch(query, batch, results, new, errors) runs after each batch; on_retry(query, batch, errors)
    runs before each resend, so callers can see failures while a batch is still being retried.
    """
    delay = default_delay() if delay is None else delay
    rotation = itertools.cycle(servers)
    concurrent = max(1, concurrent)
    totals = {'pages': 0, 'results': 0, 'new': [], 'errors': [], 'unresponsive_engines': Counter(),
              'stopped_early': False}
    attempts = empty_batch_attempts(no_new_results, pages)
    empty_batches = 0
    for start in range(1, pages + 1, concurrent):
        if stop_event is not None and stop_event.is_set():
            break
        batch = list(range(start, start + concurrent if full_batches else min(start + concurrent, pages + 1)))
        resends = 0
        while True:
            attempt_errors = []
            server = next(rotation)
            with ThreadPoolExecutor(max_workers=len(batch)) as pool:
                responses = list(pool.map(lambda p: search_page(server, query, p, engines), batch))
            for resp in responses:
                if resp['error']:
                    totals['errors'].append(resp['error'])
                    attempt_errors.append(resp['error'])
                for name, reason in resp['unresponsive_engines']:
                    totals['unresponsive_engines'][f'{name}: {reason}'] += 1
            if not any(resp['retry'] for resp in responses):
                break
            if retries is not None and resends >= retries:
                break
            resends += 1
            if on_retry:
                on_retry(query, batch, attempt_errors)
            pause = max(delay or 0, 1)
            if stop_event is not None:
                if stop_event.wait(pause):
                    break
            else:
                time.sleep(pause)
        if stop_event is not None and stop_event.is_set() and any(resp['retry'] for resp in responses):
            break
        batch_results = [r for resp in responses for r in resp['results']]
        new = store_results(database, query, batch_results)
        totals['pages'] += len(batch)
        totals['results'] += len(batch_results)
        totals['new'] += new
        if on_batch:
            on_batch(query, batch, batch_results, new, attempt_errors)
        if not batch_results and (count_first_batch or start > 1):
            empty_batches += 1
            if attempts and empty_batches >= attempts:
                totals['stopped_early'] = True
                break
        if start + concurrent <= pages and delay:
            if stop_event is not None:
                if stop_event.wait(delay):
                    break
            else:
                time.sleep(delay)
    totals['unresponsive_engines'] = dict(totals['unresponsive_engines'].most_common(10))
    totals['errors'] = totals['errors'][-10:]
    return totals


# Background Harvest Jobs
class Job:
    def __init__(self, queries, pages, concurrent, loops, no_new_results, engines, servers, database, delay):
        self.id = uuid.uuid4().hex[:8]
        self.queries, self.pages, self.concurrent, self.loops = queries, pages, concurrent, loops
        self.no_new_results, self.engines, self.servers = no_new_results, engines, servers
        self.database, self.delay = database, delay
        self.state = 'running'
        self.started = time.time()
        self.finished = None
        self.loop = 0
        self.current_query = None
        self.current_pages = None
        self.pages_done = 0
        self.results_seen = 0
        self.new_results = 0
        self.errors = 0
        self.last_error = None
        self.retrying = False
        self.recent = deque(maxlen=20)
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, name=f'dorxng-job-{self.id}', daemon=True)

    def _on_retry(self, query, batch, errors):
        self.current_query, self.current_pages = query, f'{batch[0]}-{batch[-1]}'
        self.errors += len(errors)
        self.retrying = True
        if errors:
            self.last_error = errors[-1]

    def _on_batch(self, query, batch, results, new, errors):
        self.retrying = False
        self.current_query, self.current_pages = query, f'{batch[0]}-{batch[-1]}'
        self.pages_done += len(batch)
        self.results_seen += len(results)
        self.new_results += len(new)
        self.errors += len(errors)
        if errors:
            self.last_error = errors[-1]
        for r in new:
            self.recent.append({'query': query, 'title': r['title'], 'url': r['url']})

    def _run(self):
        try:
            loop_iter = itertools.count(1) if self.loops == 0 else range(1, self.loops + 1)
            for self.loop in loop_iter:
                for index, query in enumerate(self.queries):
                    if self.stop_event.is_set():
                        break
                    # The CLI issues the first batch of each loop pass before its counter starts
                    search_pages(self.servers, query, self.pages, self.concurrent, self.engines, self.delay,
                                 self.database, self.no_new_results, self.stop_event, self._on_batch,
                                 count_first_batch=index > 0, full_batches=True, on_retry=self._on_retry)
                if self.stop_event.is_set():
                    break
            self.state = 'stopped' if self.stop_event.is_set() else 'finished'
        except Exception as error:  # report, never kill the server
            self.state = 'failed'
            self.last_error = f'{type(error).__name__}: {error}'
        finally:
            self.finished = time.time()

    def status(self):
        end = self.finished or time.time()
        return {
            'job_id': self.id, 'state': self.state, 'database': self.database,
            'queries': len(self.queries), 'loop': self.loop, 'loops': self.loops or 'infinite',
            'current_query': self.current_query, 'current_pages': self.current_pages,
            'pages_done': self.pages_done, 'results_seen': self.results_seen,
            'new_results': self.new_results, 'errors': self.errors, 'last_error': self.last_error,
            'retrying_failed_batch': self.retrying and self.state == 'running',
            'elapsed_seconds': round(end - self.started), 'mode': 'direct (no Tor)' if self.engines else 'Tor',
            'recent_new_results': list(self.recent),
        }


class JobManager:
    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()

    def start(self, **kwargs):
        with self.lock:
            running = sum(1 for j in self.jobs.values() if j.state == 'running')
            if running >= max_jobs():
                raise RuntimeError(f'{running} jobs already running (DORXNG_MAX_JOBS={max_jobs()}); stop one first')
            job = Job(**kwargs)
            self.jobs[job.id] = job
        job.thread.start()
        return job

    def get(self, job_id):
        job = self.jobs.get(job_id)
        if job is None:
            raise KeyError(f'no job "{job_id}"')
        return job

    def stop(self, job_id, wait=10):
        job = self.get(job_id)
        job.stop_event.set()
        job.thread.join(wait)
        return job

    def stop_all(self):
        for job in list(self.jobs.values()):
            job.stop_event.set()
        for job in list(self.jobs.values()):
            job.thread.join(5)
