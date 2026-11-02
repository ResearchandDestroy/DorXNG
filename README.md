# DorXNG 🔎🌎
DorXNG is a modern solution for harvesting `OSINT` data using advanced search engine operators through multiple upstream search providers. On the backend it leverages a purpose built containerized image of [SearXNG](https://docs.searxng.org/), a self-hosted, hackable, privacy focused, meta-search engine.

Our SearXNG implementation routes all search queries over the [Tor](https://www.torproject.org/) network while refreshing circuits every ten seconds with Tor's `MaxCircuitDirtiness` configuration directive. We have also disabled all of SearXNG's client side timeout features. These settings allow for evasion of search engine restrictions commonly encountered while issuing many repeated search queries.

The DorXNG client application is written in Python3, and interacts with the SearXNG API to issue search queries concurrently. It can even issue requests across multiple SearXNG instances. The resulting search results are stored in a `SQLite3` database.

![DorXNG](demo.gif)

We only enable upstream search engines that actually honor advanced search operators. Every general and web engine in SearXNG (91 of them) was tested on 2026-11-01 against [operators.lst](https://github.com/ResearchandDestroy/DorXNG/blob/main/operators.lst), a 57 query suite covering every documented operator, both over Tor and directly. Engines that ignore operators, or serve unrelated results, are disabled because they pollute the database with noise.

Enabled over Tor (default):

- `Brave`
- `DuckDuckGo` (web endpoint)
- `Google CSE`
- `GMX`
- `s1search`
- `Startpage`
- `Swisscows`

Enabled with `--no-tor` (direct):

- `Brave`
- `DuckDuckGo` (web endpoint)
- `Google CSE`
- `s1search`
- `Swisscows`
- `Yahoo`

These engines scored 92 to 100% on `site:` and `filetype:` dorks. `Yahoo` is direct only: through Tor it returns results unrelated to the query. `Bing`, `Naver`, `Yandex`, and most smaller engines ignore operators, and `Google` and `Qwant` block SearXNG entirely, so they are all disabled.

No engine strictly honors `inurl:` or `allinurl:` (they are treated as ranking hints), so expect some noise on those dorks. `site:`, `filetype:`, and `intitle:` are reliable.

For more information about what search engines SearXNG supports See: [Configured Engines](https://docs.searxng.org/user/configured_engines.html)

#### Please DO NOT use the DorXNG client application against any public SearXNG instances.

# [Buy Us A Beer! 🍺](https://www.buymeacoffee.com/researchanddestroy)

# Shout Outs 🙌

Shout out to the developers of `Tor` and `SearXNG` for making this possible. Go donate to both projects!

Shout out to the developer of [pagodo](https://github.com/opsdisk/pagodo) for the inspiration and that sweet [ghdb_scraper.py](https://github.com/opsdisk/pagodo/blob/master/ghdb_scraper.py) script!

Last but certainly not least, shout out to [j0hnny](https://en.wikipedia.org/wiki/Johnny_Long). The OG Dork. 🧠🏴‍☠

# Setup 🛠️

### LINUX ONLY ** Sorry Normies ** 🤓

Install DorXNG

```
git clone https://github.com/researchanddestroy/dorxng
cd dorxng
pip install -r requirements.txt
./DorXNG.py -h
```

Download and Run Our Custom SearXNG Docker Container (at least one). Multiple SearXNG instances can be used. Use the `--serverlist` option with DorXNG. See: [server.lst](https://github.com/ResearchandDestroy/DorXNG/blob/main/server.lst)

#### When starting multiple containers wait at least a few seconds between starting each one.
```
docker run researchanddestroy/searxng:latest
```

If you would like to build the container yourself:
```
git clone https://github.com/researchanddestroy/searxng # The URL must be all lowercase for the build process to complete
cd searxng
make container.build # Requires docker buildx (or podman)
docker run localhost/searxng/searxng:latest
```

No `buildx`? Freeze the version and build with plain `docker build`:
```
./manage pyenv.install
./local/py3/bin/python -m searx.version freeze
docker build -f container/Dockerfile -t localhost/searxng/searxng:latest .
```
By default DorXNG has a hard coded `server` variable in [parse_args.py](https://github.com/ResearchandDestroy/DorXNG/blob/main/parse_args.py) which is set to the IP address that Docker will assign to the first container you run on your machine `172.17.0.2`. This can be changed, or overwritten with `--server` or `--serverlist`.

Start Issuing Search Queries
```
./DorXNG.py -q 'search query'
```

Query the DorXNG Database
```
./DorXNG.py -D 'regex search string'
```

# Host Tor Bypass 🧅

Upstream search providers and SearXNG move fast, and our custom container can fall behind. If it breaks, you can skip it and run the official upstream SearXNG container instead. In this mode `Tor` runs on the host machine rather than inside the container.

Install Tor on the host and set the circuit refresh interval:
```
sudo pacman -S tor # or: sudo apt install tor
echo 'MaxCircuitDirtiness 10' | sudo tee -a /etc/tor/torrc
sudo systemctl enable --now tor
curl -x socks5h://127.0.0.1:9050 -s https://check.torproject.org/api/ip # Should return {"IsTor":true,...}
```

Run the latest upstream SearXNG container from the DorXNG directory, using our [settings.yml](https://github.com/ResearchandDestroy/DorXNG/blob/main/settings.yml):
```
docker pull searxng/searxng:latest
docker run --rm \
  --network host \
  -v "$(pwd)/settings.yml:/etc/searxng/settings.yml:ro" \
  searxng/searxng:latest
```

`--network host` lets the container reach the host's Tor SOCKS proxy at `127.0.0.1:9050`. The provided `settings.yml` layers on top of the container's own defaults: it routes every upstream request through Tor, enables the `json` output format, disables SearXNG's engine ban and suspension timers, enables only the validated engines, and includes the direct engines used by `--no-tor`. SearXNG refuses to start if it cannot reach Tor, so start Tor on the host first.

The upstream container serves plain HTTP on port `8080` (the `server.port` value in `settings.yml` is ignored), so point DorXNG at it with `--server`:
```
./DorXNG.py -s 'http://127.0.0.1:8080/search' -q 'search query'
```

To run more than one instance, give each one its own port with `-e SEARXNG_PORT=8081` and list them in a `--serverlist` file. Keep in mind that all of these instances share the host's single Tor circuit, unlike our custom containers, which each run their own.

#### Change the `secret_key` value in `settings.yml` before exposing this instance to anything other than localhost.

# Bypassing Tor 🚀

Tor is the default. If you would rather have SearXNG query the upstream search providers directly, add `--no-tor`:
```
./DorXNG.py -q 'site:example.com intext:example' --no-tor
```

This works with our custom container and with the Host Tor Bypass above. Both SearXNG configurations include a second, Tor free copy of each validated engine (named `<engine> direct`, disabled by default). With `--no-tor`, DorXNG asks the server for its direct engines and only uses those. Without it, nothing changes.

#### `--no-tor` exposes the public IP address of the machine running SearXNG to every search provider you query.

Direct queries are faster and some engines only work directly (`Yahoo`), but providers rate limit by IP address, so heavy use will get your IP throttled. SearXNG's own `!bang` shortcuts override `--no-tor`. To combine them, use the direct shortcuts: `!brd` (Brave), `!ddgwd` (DuckDuckGo), `!gocd` (Google CSE), `!s1d` (s1search), `!swd` (Swisscows), `!yhd` (Yahoo).

# MCP Server 🤖

DorXNG ships an [MCP](https://modelcontextprotocol.io) server (`mcp_server.py`) so AI agents like Claude Code, Claude Desktop, or any MCP client can run dork searches, drive long harvests in the background, and query the results database. It talks to the same SearXNG server(s) as the CLI, and its databases work with the CLI's `-d`, `-D`, and `-m` options.

```
pip install -r requirements.txt
```

Add it to Claude Code:
```
claude mcp add dorxng -e DORXNG_SERVER=https://172.17.0.2/search -- python3 /path/to/DorXNG/mcp_server.py
```

Or add it to any MCP client config (Claude Desktop, etc.):
```json
{
  "mcpServers": {
    "dorxng": {
      "command": "python3",
      "args": ["/path/to/DorXNG/mcp_server.py"],
      "env": {
        "DORXNG_SERVER": "https://172.17.0.2/search",
        "DORXNG_DB_DIR": "/path/to/databases"
      }
    }
  }
}
```

Agents that connect over the network can use Streamable HTTP instead of stdio. It binds to `127.0.0.1` by default, and the endpoint is `http://127.0.0.1:8765/mcp`:
```
python3 mcp_server.py --http --port 8765
```

Environment variables:

| Variable | Default | Description |
|---|---|---|
| `DORXNG_SERVER` | `https://172.17.0.2/search` | SearXNG server, or a comma separated server list (like `--serverlist`) |
| `DORXNG_DB_DIR` | current directory | Where databases are read and written. Tools only accept plain `.db` file names inside it |
| `DORXNG_DELAY` | `4` | Seconds between request batches in harvest jobs (like `--timeout`) |
| `DORXNG_MAX_JOBS` | `4` | Maximum number of harvest jobs running at once |

Tools:

| Tool | Description |
|---|---|
| `server_status` | Reachability of each server, plus its Tor, direct (`--no-tor`) and onion engines |
| `search` | Run a dork for up to 10 pages, store the results, and return the ones that are new to the database |
| `start_harvest` | Background harvest of many queries, or a bundled dork list (`ghdb` / `operators`), with pages, loops (0 = until stopped), and a no new results limit. Returns a `job_id` |
| `job_status` / `list_jobs` / `stop_job` | Follow a harvest's progress and newest results, or stop it |
| `query_database` | Regex search over titles and URLs (like `-D`) |
| `database_stats` | Row counts, results per query, and top domains |
| `list_databases` / `merge_databases` | List databases, or merge one into another (like `-m`) |
| `list_dorks` | Page through and filter the bundled GHDB dork list and `operators.lst` |

It also provides the `dorxng://operators` and `dorxng://readme` resources, and a `dork_recon` prompt that walks an agent through reconnaissance of one domain.

`search` and `start_harvest` take a `no_tor` argument. It defaults to `false`, and setting it exposes the SearXNG host's IP address to the search providers, exactly like `--no-tor`.

#### The same rule applies to agents: DO NOT point DorXNG at public SearXNG instances.

# Instructions 📖

```
-h, --help            show this help message and exit
-s SERVER, --server SERVER
                      DorXNG Server Instance - Example: 'https://172.17.0.2/search'
-S SERVERLIST, --serverlist SERVERLIST
                      Issue Search Queries Across a List of Servers - Format: Newline Delimited
-q QUERY, --query QUERY
                      Issue a Search Query - Examples: 'search query' | '!ah search query' | 'site:example.com intext:example'
-Q QUERYLIST, --querylist QUERYLIST
                      Iterate Through a Search Query List - Format: Newline Delimited
-n NUMBER, --number NUMBER
                      Define the Number of Page Result Iterations
-c CONCURRENT, --concurrent CONCURRENT
                      Define the Number of Concurrent Page Requests
-l LIMITDATABASE, --limitdatabase LIMITDATABASE
                      Set Maximum Database Size Limit - Starts New Database After Exceeded - Example: --limitdatabase 10 (10k Database Entries) - Suggested Maximum Database Size is 50k
                      when doing Deep Recursion
-L LOOP, --loop LOOP  Define the Number of Main Function Loop Iterations - Infinite Loop with 0
-d DATABASE, --database DATABASE
                      Specify SQL Database File - Default: 'dorxng.db'
-D DATABASEQUERY, --databasequery DATABASEQUERY
                      Issue Database Query - Format: Regex
-m MERGEDATABASE, --mergedatabase MERGEDATABASE
                      Merge SQL Database File - Example: --mergedatabase database.db
-t TIMEOUT, --timeout TIMEOUT
                      Specify Timeout Interval Between Requests - Default: 4 Seconds - Disable with 0
-r NONEWRESULTS, --nonewresults NONEWRESULTS
                      Specify Number of Iterations with No New Results - Default: 4 (3 Attempts) - Disable with 0
--no-tor              Bypass Tor - SearXNG Queries Upstream Search Providers Directly - Exposes the SearXNG Host IP Address to Search Providers - Default: Tor
-v, --verbose         Enable Verbose Output
-vv, --veryverbose    Enable Very Verbose Output - Displays Raw JSON Output
```

# Tips 📝

Sometimes you will hit a Tor exit node that is already shunted by upstream search providers, causing you to receive a minimal amount of search results. Not to worry... Just keep firing off queries. 😉

Onion search engines (`!ah` Ahmia, `!tch` Torch) only work while their Tor hidden service is up, and hidden services can be spotty. Ahmia has been the most reliable. Torch often times out or refuses connections for long stretches, then comes back. If you get `timeout` or `proxy error` from an onion engine, try again later. 🧅

Keep your DorXNG SQL database file and rerun your command, or use the `--loop` switch to iterate the main function repeatedly. 🔁

Most often, the more passes you make over a search query the more results you'll find. 🍻

Also keep in mind that we have made a sacrifice in speed for a higher degree of data output. This is an `OSINT` project after all. 🔎🌎

Each search query you make is being issued to `7` upstream search providers... Especially with `--concurrent` queries this generates a lot of upstream requests... So have patience.

Keep in mind that DorXNG will continue to append new search results to your database file. Use the `--database` switch to specify a database filename, the default filename is `dorxng.db`. This probably doesn't matter for most, but if you want to keep your `OSINT` investigations seperate it's there for you. 

Four concurrent search requests seems to be the sweet spot. You can issue more, but the more queries you issue at a time the longer it takes to receive results. It also increases the likelihood you receive `HTTP/429 Too Many Requests` responses from upstream search providers on that specific Tor circuit.

If you start multiple SearXNG Docker containers too rapidly Tor connections may fail to establish.
While initializing a container, a valid response from the Tor Connectivity Check function looks like this:
```
Checking Tor Connectivity..
{"IsTor":true,"IP":"<tor-exit-node>"}
```
If you see anything other than that, or if you start to see `HTTP/500` response codes coming back from the SearXNG monitor script (STDOUT in the container), kill the Docker container and spin up a new one.

`HTTP/504 Gateway Time-out` response codes within DorXNG are expected sometimes. This means the SearXNG instance did not receive a valid response back within one minute. That specific Tor curcuit is probably too slow. Just keep going!

There really isn't a reason to run a ton of these containers... Yet... 😉 How many you run really depends on what you're doing. Each container uses approximately `1.25GBs` of RAM.

Running one container works perfectly fine, except you will likely miss search results. So use `--loop` and do not disable `--timeout`.

Running multiple containers is nice because each has its own Tor curcuit thats refreshing every 10 seconds.

When running `--serverlist` mode disable the `--timeout` feature so there is no delay between requests (The default delay interval is 4 seconds).

Keep in mind that the more containers you run the more memory you will need. This goes for deep recursion too... We have disabled Python's maximum recursion limit... 🔁😉

The more recursions your command goes through without returning to `main` the more memory the process will consume. You may come back to find that the process has crashed with a `Killed` error message. If this happens your machine ran out of memory and killed the process. Not to worry though... Your database file is still good. 👍👍

If your database file gets exceptionally large it inevitably slows down the program and consumes more memory with each iteration...

Those Python Stack Frames are Thicc... 🍑😅

We've seen a marked drop in performance with database files that exceed approximately 50 thousand entries.

The `--limitdatabase` option has been implemented to mitigate some of these memory consumption issues. Use it in combination with `--loop` to break deep recursive iteration inside [iterator.py](https://github.com/ResearchandDestroy/DorXNG/blob/main/iterator.py) and restart from `main` right where you left off.

Once you have a series of database files you can merge them all (one at a time) with `--mergedatabase`. You can even merge them all into a new database file if you specify an unused filename with `--database`.

#### DO NOT merge data into a database that is currently being used by a running DorXNG process. This may cause errors and could potentially corrupt the database.

The included [query.lst](https://github.com/ResearchandDestroy/DorXNG/blob/main/query.lst) file is every dork that currently exists on the [Google Hacking Database
](https://www.exploit-db.com/google-hacking-database) (GHDB). See: [ghdb_scraper.py](https://github.com/opsdisk/pagodo/blob/master/ghdb_scraper.py)

The included [operators.lst](https://github.com/ResearchandDestroy/DorXNG/blob/main/operators.lst) file exercises every advanced search operator (`site:`, `-site:`, `filetype:`, `ext:`, `inurl:`, `allinurl:`, `intitle:`, `allintitle:`, `intext:`, `"phrases"`, `-term`, `OR`, `AND`, `( )`, `*`, `AROUND(n)`, `..` ranges, `before:`, `after:`, `related:`, and the Bing, Brave, and Yandex specific ones). It is the list we used to choose which engines to enable. Run it yourself with `./DorXNG.py -Q operators.lst` to see how your instance behaves.

We've already run through it for you... 😉 Our `ghdb.db` file contains over one million entries and counting! 🤩 You can download it here [ghdb.db](https://drive.google.com/file/d/1Fjk8D_qhbvss2nrPVDS-B6S0NtNI_Ot2/view?usp=sharing) if you'd like a copy. 😉

Example of querying the `ghdb.db` database:
```
./DorXNG.py -d ghdb.db -D '^http.*\.sql$'
```

A rewrite of `DorXNG` in `Golang` is already in the works. 😉 (`GorXNG`? | `DorXNGNG`?) 😆

We're gonna need more dorks... 😅 Check out [DorkGPT](https://www.dorkgpt.com/) 👀

# Examples 💡

Single Search Query
```
./DorXNG.py -q 'search query'
```

Concurrent Search Queries
```
./DorXNG.py -q 'search query' -c4
```

Page Iteration Mode
```
./DorXNG.py -q 'search query' -n4
```

Iterative Concurrent Search Queries
```
./DorXNG.py -q 'search query' -c4 -n64
```

Server List Iteration Mode
```
./DorXNG.py -S server.lst -q 'search query' -c4 -n64 -t0
```

Query List Iteration Mode
```
./DorXNG.py -Q query.lst -c4 -n64
```

Bypass Tor (Direct Engines Only)
```
./DorXNG.py -q 'search query' -c4 -n64 --no-tor
```

Query and Server List Iteration
```
./DorXNG.py -S server.lst -Q query.lst -c4 -n64 -t0
```

Main Function Loop Iteration Mode
```
./DorXNG.py -S server.lst -Q query.lst -c4 -n64 -t0 -L4
```

Infinite Main Function Loop Iteration Mode with a Database File Size Limit Set to 10k Entries
```
./DorXNG.py -S server.lst -Q query.lst -c4 -n64 -t0 -L0 -l10
```

Merging a Database (One at a Time) into a New Database File
```
./DorXNG.py -d new-database.db -m dorxng.db
```

Merge All Database Files in the Current Working Directory into a New Database File
```
for i in `ls *.db`; do ./DorXNG.py -d new-database.db -m $i; done
```

Query a Database
```
./DorXNG.py -d new-database.db -D 'regex search string'
```
