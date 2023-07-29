# DorXNG 🔎🌎
DorXNG is a modern solution for harvesting `OSINT` data using advanced search engine operators through multiple upstream search providers. On the backend it leverages a purpose built containerized image of [SearXNG](https://docs.searxng.org/), a self-host, hackable, privacy focused, meta-search engine.

Our SearXNG implementation routes all search queries over the [Tor](https://www.torproject.org/) network while refreshing circuits every ten seconds with Tor's `MaxCircuitDirtiness` configuration directive. We have also disabled all of SearXNG's client side timeout features. These settings allow for evasion of search engine restrictions commonly encountered while issuing many repeated search queries.

The DorXNG client application is written in Python3, and interacts with the SearXNG API to issue search queries concurrently. It can even issue requests across multiple SearXNG instances. The resulting search results are stored in a `SQLite3` database.

![DorXNG](dorxng.gif)

We have enabled every supported upstream search engine that allows advanced search operator queries:

- `Google`
- `DuckDuckGo`
- `Qwant`
- `Bing`
- `Brave`
- `Startpage`
- `Yahoo`

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

Download and Run Our Custom SearXNG Docker Container (at least one). Multiple SearXNG instances can be used. Use the `--serverlist` option with DorXNG.

#### When starting multiple containers wait a few seconds between starting each one.
```
docker run researchanddestroy/searxng:latest
```

If you would like to build the container yourself:
```
git clone https://github.com/researchanddestroy/searxng # The URL must be all lowercase for the build process to complete
cd searxng
DOCKER_BUILDKIT=1 make docker.build
docker images
docker run <image-id>
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

# Instructions 📖

```
  -s SERVER, --server SERVER
                        DorXNG Server Instance - Example: 'https://172.17.0.2/search'
  -S SERVERLIST, --serverlist SERVERLIST
                        Issue Search Queries Across a List of Servers - Format: Newline Delimited
  -q QUERY, --query QUERY
                        Issue a Search Query - Examples: 'search query' | '!tch search query' | 'site:example.com intext:example'
  -Q QUERYLIST, --querylist QUERYLIST
                        Iterate Through a Search Query List - Format: Newline Delimited
  -n NUMBER, --number NUMBER
                        Define the Number of Page Result Iterations
  -c CONCURRENT, --concurrent CONCURRENT
                        Define the Number of Concurrent Page Requests
  -L LOOP, --loop LOOP  Define the Number of Main Function Loop Iterations
  -t TIMEOUT, --timeout TIMEOUT
                        Specify Timeout Interval Between Requests - Default: 4 Seconds - Disable with 0
  -d DATABASE, --database DATABASE
                        Specify SQL Database File - Default: 'dorxng.db'
  -D DATABASEQUERY, --databasequery DATABASEQUERY
                        Issue Database Query - Format: Regex
  -r NONEWRESULTS, --nonewresults NONEWRESULTS
                        Specify Number of Iterations with No New Results - Default: 4 (3 Attempts) - Disable with 0
  -v, --verbose         Enable Verbose Output
  -vv, --veryverbose    Enable Very Verbose Output - Displays Raw JSON Output
```

# Tips 📝

Sometimes you will hit a Tor exit node that is already shunted by upstream search providers, causing you to receive a minimal amount of search results. Not to worry... Just keep firing off queries. 😉

Keep your DorXNG SQL database file and rerun your command, or use the `--loop` switch to iterate the main function repeatedly. 🔁

Most often, the more passes you make over a search query the more results you'll find. 🍻

Also keep in mind that we have made a sacrifice in speed for a higher degree of data output. This is an `OSINT` project after all. 🔎🌎

Each search query you make is being issued to `7` upstream search providers... Especially with `--concurrent` queries this generates a lot of upstream requests... So have patience.

Keep in mind that DorXNG will continue to append new search results to the `dorxng.db` database file if you don't use the `--database` switch to specify a different one. This probably doesn't matter for most, but if you want to keep your `OSINT` investigations seperate it's there for you. 

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

Running one container works perfectly fine. Running multiple is nice because each has its own Tor curcuit thats refreshing every 10 seconds.

When running `--serverlist` mode disable the `--timeout` feature so there is no delay between requests (The default delay interval is 4 seconds).

Keep in mind that the more containers you run the more memory you will need. This goes for deep recursion too...

The more recursions your command goes through the more memory the process will consume. You may come back to find that the process has crashed with a `Killed` error message. If this happens your machine ran out of memory and killed the process. Not to worry though... Your database file is still good. 👍👍

If your database file gets exceptionally large it inevitably slows down the program and consumes more memory with each iteration...

Those Python Stack Frames are Thicc. 🍑😅

We've seen a marked drop in performance with database files that exceed approximately 50 thousand entries.

The included [query.lst](https://github.com/ResearchandDestroy/DorXNG/blob/main/query.lst) file is every dork that currently exists on the [Google Hacking Database
](https://www.exploit-db.com/google-hacking-database). See: [ghdb_scraper.py](https://github.com/opsdisk/pagodo/blob/master/ghdb_scraper.py)

However, when using `--querylist` iteration mode its best to use lists that are shorter than the included [query.lst](https://github.com/ResearchandDestroy/DorXNG/blob/main/query.lst)... With one instance on a machine with `16GBs` of memory we were able to iterate over approximately six thousand queries using `./DorXNG.py -S server.lst -Q query.lst -c4 -n64 -t0` before the process crashed.

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

Query and Server List Iteration
```
./DorXNG.py -S server.lst -Q query.lst -c4 -n64 -t0
```

Main Function Loop Iteration Mode
```
./DorXNG.py -S server.lst -Q query.lst -c4 -n64 -t0 -L4
```
