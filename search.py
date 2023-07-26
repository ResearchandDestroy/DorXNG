import concurrent.futures
import requests

# Search Query Function
def issue_search(args, server, server_list, previous_server,
                 search_params, search_query,
                 concurrent_connections, concurrent_params):

    # Disable Certificate Validation Warning
    requests.packages.urllib3.disable_warnings()

    # Define User-Agent Header
    headers = {
        'User-Agent': 'DorXNG',
    }

    # If Concurrent URL List is Populated Run Concurrent Requests
    if concurrent_params != []:

        # If Server List Mode is Enabled
        if args.serverlist is not None:

            # Detect When a Server List is in Use
            # and Set Server Variable For First Pass
            if args.serverlist is not None and server_list != [] and not previous_server:
                server = server_list[0]

            # Reset Server to First Entry
            if previous_server == len(server_list) + 1:
                previous_server = 0
                server = server_list[0]

            # Increment Previous Server on the First Pass
            if args.serverlist is not None and previous_server == 0:
                previous_server = server_list.index(server) + 1

            # Increment Previous Server Up to Last List Entry Then Reset to Zero
            if previous_server != 0:
                server = server_list[previous_server - 1]
                previous_server = server_list.index(server) + 2

            try:
                # Issue Concurrent Search Queries with Server List Iteration
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    results = [executor.submit(requests.post, server, params, headers=headers, verify=False) for params in concurrent_params]
                    concurrent.futures.wait(results)

                # Unpack Concurrent Search Results and Look for HTTP Errors
                for number in range(concurrent_connections):
                    responses = results[number].result()
                    responses.raise_for_status()

            # HTTP Error Handling for Concurrent Requests with Server List Iteration
            except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as error:
                print("\nReceived an Invalid Response..")
                print(error)
                print("Trying Next Server..\n")

                # Issue Iterated Search Query
                results = issue_search(args, server, server_list, previous_server,
                             search_params, search_query, concurrent_connections, concurrent_params)

                return results

            return results, previous_server

        else:

            try:
                # Issue Concurrent Search Queries
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    results = [executor.submit(requests.post, server, params, headers=headers, verify=False) for params in concurrent_params]
                    concurrent.futures.wait(results)

                # Unpack Concurrent Search Results and Look for HTTP Errors
                for number in range(concurrent_connections):
                    responses = results[number].result()
                    responses.raise_for_status()

            # HTTP Error Handling for Concurrent Requests
            except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as error:
                if args.querylist is not None:
                    print("\nReceived an Invalid Response..")
                    print(error)
                    print("Trying Next Server..\n")

                    # Reset Server to First Entry
                    if previous_server == len(server_list) + 1:
                        previous_server = 0
                        server = server_list[0]

                    # Increment Previous Server on the First Pass
                    if args.serverlist is not None and previous_server == 0:
                        previous_server = server_list.index(server) + 1

                    # Increment Previous Server Up to Last List Entry Then Reset to Zero
                    if previous_server != 0:
                        server = server_list[previous_server - 1]
                        previous_server = server_list.index(server) + 2

                    # Issue Iterated Search Query
                    results = issue_search(args, server, server_list, previous_server,
                                 search_params, search_query, concurrent_connections, concurrent_params)

                    return results, previous_server

                else:
                    print("\nAn Error Occurred..\n")
                    print(error)
                    if args.loop is not None:
                        return
                    else:
                        exit(1)

            return results

    else:

        try:
            # Issue Single Request
            results = requests.post(server, search_params, headers=headers, verify=False)
            results.raise_for_status()

        # HTTP Error Handling for Single Requests
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as error:
            if args.querylist is not None:
                print("\nReceived an Invalid Response..")
                print(error)
                print("Retrying Request..\n")

                # If Server List Mode is Enabled
                if args.serverlist is not None:
                
                    # Reset Server to First Entry
                    if previous_server == len(server_list) + 1:
                        previous_server = 0
                        server = server_list[0]

                    # Increment Previous Server on the First Pass
                    if args.serverlist is not None and previous_server == 0:
                        previous_server = server_list.index(server) + 1

                    # Increment Previous Server Up to Last List Entry Then Reset to Zero
                    if previous_server != 0:
                        server = server_list[previous_server - 1]
                        previous_server = server_list.index(server) + 2

                # Issue Iterated Search Query
                results = issue_search(args, server, server_list, previous_server,
                             search_params, search_query, concurrent_connections, concurrent_params)

                return results, previous_server

            else:
                print("\nAn Error Occurred..\n")
                print(error)
                if args.loop is not None:
                    return
                else:
                    exit(1)

        return results
