#!/usr/bin/python3
# DorXNG -- Next Generation DorX. Built by Dorks, for Dorks. 🤓
#
# https://github.com/researchanddestroy/DorXNG
# https://github.com/researchanddestroy/searxng
#
# This application is for research and educational purposes only.
# LINUX ONLY ** Sorry Normies **
#
# by: unixnerd -- RaD 🥼🥽 ➕ 💻🔨 🟰 🔥
# https://researchanddestroy.technology
#
# Buy me a beer! 🍻
# https://www.buymeacoffee.com/researchanddestroy
#      _________
#     / ======= \
#    /___________\
#   | ___________ |
#   | |~# _     | |
#   | |         | |
#   | |_________| |________________________
#   \=____________/  Research and Destroy  )
#   / """"""""""" \                       /
#  / ::::::::::::: \                  =D-'
# (_________________)

# Import Modules
import signal
import sys
import features
import parse_args
import url_construction
import iterator
import search
import data_handling

# Main Function
def main(args, server, server_list, query_list, previous_server,
         search_params, search_query, page_iteration_mode,
         page_iteration_number, page_number, reset_page_number,
         concurrent_connections, concurrent_params, concurrent_pages,
         database_name, database_file, detect_database, exceeded_database,
         database_results, timer, no_new_results_counter, results_data,
         previous_results, total_current_results):

    # Increase Maximum Recursion Depth
    sys.setrecursionlimit(10 ** 9)

    # Print Banner
    features.banner()

    # Graceful Shutdown Function
    def exit_handler(signum, frame):
        print("\nCaught Ctrl+C.. Exiting..")
        exit (0)

    # Graceful Shutdown Handler
    signal.signal(signal.SIGINT, exit_handler)

    # Check Verbosity
    features.verbosity(args, page_iteration_mode,
                       query_list, server_list)

    # Check for Previous Database
    previous_results, detect_database = data_handling.previous_database(args, database_name, database_file,
                                                                        detect_database, database_results,
                                                                        previous_results)

    # Handle Database Query Requests
    if args.databasequery:
        data_handling.database_query(args, database_name, previous_results)

    # If Previous Database Detected
    if detect_database is True:
        # Create Formated List of Current Results
        for result in previous_results:
            current_result = "{} | {}".format(result[0], result[1])
            total_current_results.append(current_result)

        # Reset Previous Results
        previous_results = []

        # Reset Detect Database
        detect_database = False

    # If Query List Iteration Mode Print First Query
    if args.querylist is not None:
        print('Query: "' + str(args.query) + '"\n')

    # If Concurrency Mode Enabled Iterate Through Construct URL N Number of Times
    if concurrent_connections > 0:
        if page_iteration_mode is True:
            page_iteration_number = args.number

        concurrent_params, concurrent_pages, page_number, reset_page_number = url_construction.concurrent_url_params_construction(
                args, page_iteration_mode, page_iteration_number, page_number,
                reset_page_number, server, previous_server, server_list,
                concurrent_connections, concurrent_params, concurrent_pages,
                search_params, search_query)

    else:
        # Gather Variable Definition from Construct URL
        page_iteration_number, reset_page_number, server, previous_server, search_params, search_query = url_construction.construct_url(
                args, page_iteration_mode, page_iteration_number, reset_page_number,
                server, previous_server, server_list, concurrent_connections,
                concurrent_pages, search_params, search_query)

    # Issue Search Query
    results = search.issue_search(args, server, server_list, previous_server, page_iteration_mode,
                                  search_params, search_query, concurrent_connections, concurrent_params)

    # Prepare Data
    results_data, list_of_raw_results, previous_server  = data_handling.prepare_data(
            results, concurrent_connections, previous_server)

    # Store Search Results in SQL
    database_results = data_handling.store_results(
            args, database_name, database_file, results_data)

    # Output Search Results to STDOUT
    exceeded_database, previous_results, total_current_results = data_handling.output_results(
            args, concurrent_connections, results, list_of_raw_results,
            database_name, database_results, exceeded_database,
            previous_results, total_current_results)

    # If Page Iteration Mode or Query List Option is Enabled Go to Page Iterator
    if page_iteration_mode is True or args.querylist is not None:
        args = iterator.page_iterator(args, database_name, database_file, detect_database,
                      exceeded_database, page_iteration_mode, page_iteration_number,
                      page_number, reset_page_number, concurrent_connections,
                      concurrent_params, concurrent_pages, timer, server,
                      previous_server, server_list, query_list, search_params,
                      search_query, no_new_results_counter, results_data,
                      database_results, previous_results, total_current_results)

    # Summarize Results
    if args.loop == 0 or args.loop is not None:
        pass
    else:
        print('\nTOTAL NUMBER OF RESULTS: ' + str(len(database_results)))

    # Return Args if Main Loop Function Iteration Mode
    return args


# Initialize Variables
server_list = []
query_list = []
previous_server = int()
search_params = {}
search_query = str()
page_iteration_number = int()
page_number = int()
reset_page_number = False
concurrent_params = []
concurrent_pages = int() 
database_file = str()
detect_database = False
exceeded_database = False
database_results = [] 
no_new_results_counter = int()
results_data = []
previous_results = []
total_current_results = []

# Define and Gather Arguments Before Main
args, server, page_iteration_mode, timer, database_name, server_list, query_list, concurrent_connections = parse_args.parse_args()

# Save Original Page Iteration Number Before Entering Main
initial_page_iteration_number = args.number

# If Main Function Loop Iteration Mode Enabled
if args.loop == 0 or args.loop is not None:

    # If Infinite Main Function Loop Iteration Mode
    if args.loop == 0:
        while args.loop == 0:

            # Reset Page Number Per Iteration
            args.number = initial_page_iteration_number

            # Execute Main Function N Number of Times
            if __name__ == '__main__':
                args = main(args, server, server_list, query_list, previous_server,
                            search_params, search_query, page_iteration_mode,
                            page_iteration_number, page_number, reset_page_number,
                            concurrent_connections, concurrent_params, concurrent_pages,
                            database_name, database_file, detect_database, exceeded_database,
                            database_results, timer, no_new_results_counter, results_data,
                            previous_results, total_current_results)

    # If Limited Main Function Loop Iteration Mode
    elif args.loop > 0:

        for loop in range(args.loop):

            # Reset Page Number Per Iteration
            args.number = initial_page_iteration_number

            # Execute Main Function N Number of Times
            if __name__ == '__main__':
                args = main(args, server, server_list, query_list, previous_server,
                            search_params, search_query, page_iteration_mode,
                            page_iteration_number, page_number, reset_page_number,
                            concurrent_connections, concurrent_params, concurrent_pages,
                            database_name, database_file, detect_database, exceeded_database,
                            database_results, timer, no_new_results_counter, results_data,
                            previous_results, total_current_results)
        exit(0)
    
else:

    # Execute Main Function
    if __name__ == '__main__':
        main(args, server, server_list, query_list, previous_server,
             search_params, search_query, page_iteration_mode,
             page_iteration_number, page_number, reset_page_number,
             concurrent_connections, concurrent_params, concurrent_pages,
             database_name, database_file, detect_database, exceeded_database,
             database_results, timer, no_new_results_counter, results_data,
             previous_results, total_current_results)
