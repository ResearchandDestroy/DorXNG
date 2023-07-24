# Banner
def banner():
    print(
            "    ____            _  __ _   ________" + '\n'
            "   / __ \____  ____| |/ // | / / ____/" + '\n'
            "  / / / / __ \/ ___/   //  |/ / / __" + '\n'
            " / /_/ / /_/ / /  /   |/ /|  / /_/ /" + '\n'
            "/_____/\____/_/  /_/|_/_/ |_/\____/" + '\n'
         )


# Verbosity
def verbosity(args, page_iteration_mode,
              query_list, server_list):

    # Verbose Output
    if args.verbose or args.veryverbose is True:
        print('\nVerbose Logs:')
        print('CLI Args: ' + str(args))
        print('Concurrent Page Requests: ' + str(args.concurrent))
        print('Page Iteration Mode: ' + str(page_iteration_mode))
        print('Query List Iteration Mode: ' + str(bool(args.querylist)))
        print('Server List Iteration Mode: ' + str(bool(args.serverlist)))

        if page_iteration_mode is True:
            print('Page Iterations: ' + str(args.number))
            print('Timer: ' + str(args.timeout) + ' Seconds')

        if bool(args.querylist) is True:
            print('Query List: ' + str(query_list))

        if bool(args.serverlist) is True:
            print('Server List: ' + str(server_list))

        print('Search Query: ' + '"' + args.query + '"' + '\n')
