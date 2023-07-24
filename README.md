# DorXNG
DorXNG is a next generation solution for harvesting OSINT data using advanced search engine operators through multiple upstream search providers. On the backend it leverages a heavily modified and containerized image of SearXNG, a self-host, hackable, privacy focused meta-search engine.

Our SearXNG implementation routes all search queries over the Tor network while refreshing circuits every ten second to evade search engine restrictions and increase anonymity. The DorXNG client application is written in Python3, and interacts with the SearXNG API to issue search queries concurrently. The resulting search results are stored in a SQL database.

[Buy Us A Beer! 🍺](https://www.buymeacoffee.com/researchanddestroy)

# Setup

LINUX ONLY ** Sorry Normies **

Install DorXNG

```
git clone https://github.com/researchanddestroy/dorxng
cd dorxng
pip install -r requirements.txt
./DorXNG.py -h
```

Download and Run Our Custom SearXNG Docker Container (at least one). Multiple SearXNG instances can be used. Use the --serverlist option with DorXNG.

When starting multiple containers wait 10 seconds between starting each one.
```
docker run researchanddestroy/searxng:latest
```

If you would like to build the container yourself:
```
git clone https://github.com/researchanddestroy/searxng **The URL must be all lowercase for the build process to complete**
cd searxng
make docker.build
docker images
docker run <image-id>
```

Start Issuing Search Queries
```
./DorXNG.py -q 'search query'
```

Query the DorXNG Database
```
./DorXNG.py -D 'regex search string'
```

# Tips

Sometimes you will hit a Tor exit node that is already shunted by upstream search providers. Not to worry.. Just keep firing off queries. 😉

Keep your DorXNG SQL database file and rerun your command, or use the --loop switch to iterate the main function repeatedly. 🔁

The more passes you have over a search query the more results you'll find. 🍻

# Instructions

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

# Examples

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
./DorXNG.py -q 'search query' -c4 -n16
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
