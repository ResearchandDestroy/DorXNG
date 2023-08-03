import argparse
import sys

# CLI Arguments
def parse_args():

    # Define CLI Arguments
    parser = argparse.ArgumentParser()
    server_group = parser.add_mutually_exclusive_group()
    query_group = parser.add_mutually_exclusive_group()
    verbosity_group = parser.add_mutually_exclusive_group()
    server_group.add_argument('-s',
                        '--server',
                        type=str,
                        help='DorXNG Server Instance - '
                        'Example: \'https://172.17.0.2/search\'')

    server_group.add_argument('-S',
                        '--serverlist',
                        type=str,
                        help='Issue Search Queries Across a List of Servers - '
                        'Format: Newline Delimited')

    query_group.add_argument('-q',
                        '--query',
                        type=str,
                        help='Issue a Search Query - Examples: '
                        '\'search query\' | '
                        '\'!tch search query\' | '
                        '\'site:example.com intext:example\'')

    query_group.add_argument('-Q',
                        '--querylist',
                        type=str,
                        help='Iterate Through a Search Query List - '
                        'Format: Newline Delimited')

    parser.add_argument('-n',
                        '--number',
                        type=int,
                        default=1,
                        help='Define the Number of Page Result Iterations')

    parser.add_argument('-c',
                        '--concurrent',
                        type=int,
                        help='Define the Number of Concurrent Page Requests')

    parser.add_argument('-l',
                        '--limitdatabase',
                        type=int,
                        help='Set Maximum Database Size Limit - '
                        'Starts New Database After Exceeded - '
                        'Example: --limitdatabase 10 (10k Database Entries) - '
                        'Suggested Maximum Database Size is 50k when doing Deep Recursion')

    parser.add_argument('-L',
                        '--loop',
                        type=int,
                        help='Define the Number of Main Function Loop Iterations - '
                        'Infinite Loop with 0')

    parser.add_argument('-d',
                        '--database',
                        type=str,
                        default='dorxng.db',
                        help='Specify SQL Database File - '
                        'Default: \'dorxng.db\'')

    parser.add_argument('-D',
                        '--databasequery',
                        type=str,
                        help='Issue Database Query - '
                        'Format: Regex')

    parser.add_argument('-m',
                        '--mergedatabase',
                        type=str,
                        help='Merge SQL Database File')

    parser.add_argument('-t',
                        '--timeout',
                        type=int,
                        default=4,
                        help='Specify Timeout Interval Between Requests - '
                        'Default: 4 Seconds - Disable with 0')

    parser.add_argument('-r',
                        '--nonewresults',
                        type=int,
                        default='4',
                        help='Specify Number of Iterations with No New Results - '
                        'Default: 4 (3 Attempts) - Disable with 0')

    verbosity_group.add_argument('-v',
                        '--verbose',
                        help='Enable Verbose Output',
                        action='store_true')

    verbosity_group.add_argument('-vv',
                        '--veryverbose',
                        help='Enable Very Verbose Output - '
                        'Displays Raw JSON Output',
                        action='store_true')

    # Parse CLI Arguments
    args = parser.parse_args()

    # If no CLI Arguments Were Given Print Help
    if len(sys.argv) == 1:
        parser.print_help()
        exit(0)

    # HARD CODE ME OR USE -s/--server OR -S/--serverlist
    server = 'https://172.17.0.2/search'

    # Set Server via -s/--server CLI Switch
    if args.server is not None:
        server = args.server

    # Set Server to an Empty String if Not Set with -s or Hardcoded
    if args.server is None and server is None:
        server = str()

    # Handle Page Number Iteration Option
    if args.number != 1:
        page_iteration_mode = True

    else:
        page_iteration_mode = False

    # Handle Request Timer Option
    if args.timeout is not None:
        timer = args.timeout

    # Handle Database File Option
    if args.database is not str('dorxng.db'):
        database_name = args.database
    else:
        database_name = 'dorxng.db'

    # Handle Server List Option
    if args.serverlist is not None:
        with open(args.serverlist) as file:
            server_list = [line.rstrip() for line in file]
    else:
        server_list = []

    # Handle Query List Option
    if args.querylist is not None:
        with open(args.querylist) as file:
            query_list = [line.rstrip() for line in file]
        args.query = query_list[0]
    else:
        query_list = []

    # Handle Concurrency Option
    if args.concurrent is not None:
        concurrent_connections = args.concurrent
    else:
        concurrent_connections = int()

    # Return CLI Arguments to Main
    return args, server, page_iteration_mode, timer, database_name, server_list, query_list, concurrent_connections
