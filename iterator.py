import time
import url_construction
import features
import search
import data_handling

# Page Iterator Function
def page_iterator(args, database_name, database_file, page_iteration_mode,
                  page_iteration_number, page_number, reset_page_number, concurrent_connections,
                  concurrent_params, concurrent_pages, timer, server,
                  previous_server, server_list, query_list, search_params,
                  search_query, no_new_results_counter, results_data,
                  database_results, previous_results, total_current_results):

    # Check Verbosity
    features.verbosity(args, page_iteration_mode,
                       page_iteration_number, search_query,
                       query_list, server_list)

    # If Page Iteration Mode is Disabled
    # Single Page or Concurrent Page Query List Iteration is Enabled
    if page_iteration_mode is False:

        # Disable No New Results Counter in These Modes
        no_new_results_counter = 0

        # If Current Query is Last in Query List Exit
        if args.query == query_list[-1]:
            # Summarize Results
            print('\nTOTAL NUMBER OF RESULTS: ' + str(len(total_current_results)) + '\n')
            if args.loop is not None:
                return
            else:
                exit(0)

        # Reset Page Number, Concurrent Pages
        # and Increment Query from List
        else:
            args.number = 1
            concurrent_pages = 0
            args.query = query_list[query_list.index(args.query) + 1]
            print('\nQuery: ' + '"' + str(args.query) + '"''\n')
            reset_page_number = True

    # Set No New Results Counter
    if not no_new_results_counter and page_iteration_mode is True:

        # If No New Search Results Counter is Zero it is Disabled
        if args.nonewresults == 0:
            pass

       # If No New Search Results Counter is 4 it is Default
        elif args.nonewresults == 4:
            no_new_results_counter = args.nonewresults

        # Anything Else is User Defined
        else:
            no_new_results_counter = args.nonewresults + 1

    # If Current Page Number
    # is Equal to Page Total Exit
    if page_iteration_mode is not False:
        if args.number == page_iteration_number or concurrent_connections * concurrent_pages >= page_iteration_number:
            # If Query List Iteration Mode is Enabled
            if args.querylist is not None:
                # If Current Query is Last in Query List Exit
                if args.query == query_list[-1]:
                    # Summarize Results
                    print('\nTOTAL NUMBER OF RESULTS: ' + str(len(total_current_results)))
                    if args.loop is not None:
                        return
                    else:
                        exit(0)
                # Reset Concurrent Pages, Page Number
                # and Increment Query from List
                else:
                    no_new_results_counter = args.nonewresults
                    args.number = 1
                    concurrent_pages = 0
                    args.query = query_list[query_list.index(args.query) + 1]
                    print('\nQuery: ' + '"' + str(args.query) + '"''\n')
                    reset_page_number = True
            else:
                # Summarize Results
                print('\nTOTAL NUMBER OF RESULTS: ' + str(len(total_current_results)))
                if args.loop is not None:
                    return
                else:
                    exit(0)

    # If Concurrency Mode Enabled Iterate Through Construct URL N Number of Times
    if concurrent_connections > 0:

        # Reset Concurrent Params for
        # Concurrent Query List Iteration Mode
        concurrent_params = []

        concurrent_params, concurrent_pages, page_number, reset_page_number = url_construction.concurrent_url_params_construction(
                args, page_iteration_mode, page_iteration_number, page_number, reset_page_number, server,
                previous_server, server_list, concurrent_connections,
                concurrent_params, concurrent_pages, search_params, search_query)
    else:
        # Construct the new iterated URL
        page_iteration_number, reset_page_number, server, previous_server, search_params, search_query = url_construction.construct_url(
                args, page_iteration_mode, page_iteration_number, reset_page_number,
                server, previous_server, server_list,
                concurrent_connections, concurrent_pages,
                search_params, search_query)

    # Default Timer is 4 seconds,
    # Increase Request Timeout Value with -t
    # Disable Timeout with -t 0/--timeout 0
    if timer != 4:
        time.sleep(timer)
    elif timer == 0:
        pass
    else:
        time.sleep(4)

    # Issue Iterated Search Query
    results = search.issue_search(args, server, server_list, previous_server,
                                  search_params, search_query, concurrent_connections, concurrent_params)

    # Prepare Results
    results_data, list_of_raw_results, previous_server = data_handling.prepare_data(results, concurrent_connections, previous_server)

    # Store Search Results in SQL
    database_results = data_handling.store_results(
            args, database_name, database_file, results_data)

    # If Results Data is Not Empty
    if results_data != []:

        # Set Current Results to Previous and Reset Current
        previous_results = total_current_results
        total_current_results = []

        # Output Results
        data_handling.output_results(args, concurrent_connections,
                       results, list_of_raw_results, database_results,
                       previous_results, total_current_results)

    else:

        # If No Current Results, Total Current Results, or Previous Results is Empty Pass
        if results_data == []:
            pass
        else:
            # Set Current Results to Previous and Reset Current
            previous_results = total_current_results

        # If No New Results Counter is Zero it is Disabled
        if args.nonewresults == 0 or no_new_results_counter == 0:
            print("\nNo Results Detected!")

        # If No New Results Detected Decrement Duplicate Results Counter
        else:
            no_new_results_counter = no_new_results_counter - 1
            print('\nNo Results Detected! Retry Counter is now: '
                  + str(no_new_results_counter))

        # If No New Results Counter is Zero Exit
        if no_new_results_counter == 1:
            print('\nMaximum Duplicate Search Results Reached..')
            # If Query List Iteration Mode is Enabled
            if args.querylist is not None:
                # If Current Query is Last in Query List Exit
                if args.query == query_list[-1]:
                    # Summarize Results
                    print('\nTOTAL NUMBER OF RESULTS: ' + str(len(total_current_results)))
                    if args.loop is not None:
                        return
                    else:
                        exit(0)
                # Reset Page Number, Concurrent Pages
                # and Increment Query from List
                else:
                    no_new_results_counter = args.nonewresults
                    args.number = 1
                    concurrent_pages = 0
                    args.query = query_list[query_list.index(args.query) + 1]
                    print('\nQuery: "' + str(args.query) + '"\n')
                    reset_page_number = True
            else:
                # Summarize Results
                print('\nTOTAL NUMBER OF RESULTS: ' + str(len(total_current_results)))
                if args.loop is not None:
                    return
                else:
                    exit(0)

    # Continue Iteration
    page_iterator(args, database_name, database_file, page_iteration_mode,
                  page_iteration_number, page_number, reset_page_number, concurrent_connections,
                  concurrent_params, concurrent_pages, timer, server,
                  previous_server, server_list, query_list, search_params,
                  search_query, no_new_results_counter, results_data,
                  database_results, previous_results, total_current_results)
