import re
import urllib.parse

# Construct URL
def construct_url(args, page_iteration_mode, page_iteration_number,
                  reset_page_number, server, previous_server,
                  server_list, concurrent_connections,
                  concurrent_pages, search_params, search_query):

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

    # If Page Number is Less Than
    # Page Iterations Increment Page Number
    if reset_page_number is True:
        reset_page_number = False
    elif args.number < page_iteration_number:
        args.number = args.number + 1

    # If Page Iterator Mode Enabled and
    # Page Iteration Number is Empty Store
    # Iteration Number and Set Page Number to One
    if not concurrent_connections and page_iteration_mode is True and not page_iteration_number:
        page_iteration_number = args.number
        args.number = 1

    # Handle Special SearXNG Search Operators
    if re.match(r"^\!", args.query):
        special_search_operator = True
        args.query = args.query[1:]
    else:
        special_search_operator = False

    # Construct URL Encoded Parameters
    search_params = {'q': args.query, 'format': 'json', 'pageno': args.number}
    encoded_params = urllib.parse.urlencode(search_params)

    # If Special Search Operator Used Add '!' After URL Encoding
    if special_search_operator is True:
        encoded_params = encoded_params[:2] + '!' + encoded_params[2:]
        args.query = args.query[:0] + '!' + args.query[0:]
        search_params = {'q': args.query, 'format': 'json', 'pageno': args.number}

    # Construct Search Query URL
    search_query = server + '?' + encoded_params

    # Return Results
    return page_iteration_number, reset_page_number, server, previous_server, search_params, search_query


def concurrent_url_params_construction(args, page_iteration_mode, page_iteration_number,
                                       page_number, reset_page_number, server, previous_server,
                                       server_list, concurrent_connections, concurrent_params,
                                       concurrent_pages, search_params, search_query):

    if page_iteration_mode is True:

        # If Reset Page Number is True Reset Counters
        if reset_page_number is True:
            args.number = concurrent_connections
            page_number = 0 
            concurrent_pages = 0
            reset_page_number = False

        # Set Concurrent Pages:
        if concurrent_pages == 0:
            concurrent_pages = 1
        elif concurrent_pages >= 1:
            concurrent_pages = concurrent_pages + 1

        # Reset Concurrent_Params
        if concurrent_params != []:
            concurrent_params = []

        # Generate N Number of URL Params for Concurrency Mode
        concurrent_url_params_list = [construct_url(
            args, page_iteration_mode, page_iteration_number, reset_page_number,
            server, previous_server, server_list, concurrent_connections,
            concurrent_pages, search_params, search_query)
                for args.number in range(page_number, concurrent_connections * concurrent_pages)]

    if page_iteration_mode is False:

        # Generate N Number of URL Params for Concurrency Mode
        concurrent_url_params_list = [construct_url(
            args, page_iteration_mode, page_iteration_number, reset_page_number,
            server, previous_server, server_list, concurrent_connections,
            concurrent_pages, search_params, search_query)
                for args.number in range(1, concurrent_connections + 1)]

    # Generate Concurrent Search Params List
    for params in concurrent_url_params_list:
        concurrent_params.append(params[4])
        reset_page_number = params[1]

    # Set Page Number to Last Page Queried
    last_dict = concurrent_params[-1]
    page_number = last_dict['pageno']

    return concurrent_params, concurrent_pages, page_number, reset_page_number
