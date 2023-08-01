import os
import re
import sqlite3
import pprint

def database_query(args, database_name, previous_results):

    # Check if Database File Exists
    if os.path.exists('./' + database_name):

        # Define Local Variables
        database_results = []
        results_found = []

        # Search for Matching Results
        # Only Match Title or URL
        for entry in previous_results:
            if re.search(args.databasequery, entry[1], re.IGNORECASE) or re.search(args.databasequery, entry[2], re.IGNORECASE):
                results = "{} | {} | {}".format(entry[0], entry[1], entry[2])
                results_found.append(results)

        # Print Matching Results
        for result in results_found:
            print(result)

        print('\n' + str(len(results_found)) + ' Results Found')
        exit(0)

    else:
        print("No Database Detected..")
        exit(1)

# Previous Database Function
def previous_database(args, database_name, database_file, detect_database, database_results, previous_results):

    # Check if Database File Exists
    if os.path.exists('./' + database_name):

        # If Merge Database
        if args.mergedatabase:

            # Check if Database File Exists
            if os.path.exists('./' + args.mergedatabase):

                # Create Database Connection and Cursor
                connection = sqlite3.connect(args.mergedatabase)
                cursor = connection.cursor()

            else:

                print('No Database ' + str(args.mergedatabase) + ' Detected..')
                exit(1)

        else:

            # Create Database Connection and Cursor
            connection = sqlite3.connect(database_name)
            cursor = connection.cursor()

        # If Database Merge or Database Query Mode
        if args.databasequery or args.mergedatabase:

            # Query Data from Database
            previous_results = cursor.execute(
                    'SELECT query, title, url FROM search_results').fetchall()

            # Close Database Connection
            connection.close()

            # If Merge Database Pass
            if args.mergedatabase:

                pass

            else:

                # If Previous Database Detected Set to True
                detect_database = True

                return previous_results, detect_database

        else:

            # Query Data from Database
            previous_results = cursor.execute(
                    'SELECT title, url FROM search_results').fetchall()

            # Close Database Connection
            connection.close()
        
            # If Previous Database Detected Set to True
            detect_database = True
        
            return previous_results, detect_database

        # If Merge Database Send Previous Results to Database
        if args.mergedatabase:
            
            # Store Search Results in SQL
            database_results = store_results(
                    args, database_name, database_file, previous_results)

            print("Database Merged")
            print('TOTAL NUMBER OF RESULTS: ' + str(len(database_results)))
            exit(0)

    else:

        # If Merge Database Send Previous Results to Database
        if args.mergedatabase:

            # Check if Database File Exists
            if os.path.exists('./' + args.mergedatabase):

                # Create Database Connection and Cursor
                connection = sqlite3.connect(args.mergedatabase)
                cursor = connection.cursor()

            else:

                print('No Database ' + str(args.mergedatabase) + ' Detected..')
                exit(1)

            # Query Data from Database
            previous_results = cursor.execute(
                    'SELECT query, title, url FROM search_results').fetchall()

            # Close Database Connection
            connection.close()

            # Store Search Results in SQL
            database_results = store_results(
                    args, database_name, database_file, previous_results)

            print("Database Merged")
            print('TOTAL NUMBER OF RESULTS: ' + str(len(database_results)))
            exit(0)

        return previous_results, detect_database


# Prepare Data Function
def prepare_data(results, concurrent_connections, previous_server):

    # Initialize the Results Data List
    list_of_raw_results = []
    list_of_results = []
    results_list = []
    results_data = []

    # If Results are from Concurrent Requests Unpack Them
    if type(results) == list:
        for number in range(concurrent_connections):
            responses = results[number].result()
            list_of_raw_results.append(responses.json())
            list_of_results.append(responses.json()['results'])

        # Create a List of Dictionaries from Each Request
        for entry in list_of_results:
            for results in entry:
                    results_entry = {'title': results['title'],
                                     'url': results['url']}
                    results_data.append(results_entry)

    else:
        if type(results) == tuple:

            # Unpack Nested Results Data
            raw_results, previous_server = results

            for number in range(concurrent_connections):
                responses = raw_results[number].result()
                list_of_raw_results.append(responses.json())
                list_of_results.append(responses.json()['results'])

            # Create a List of Dictionaries from Each Request
            for entry in list_of_results:
                for results in entry:
                        results_entry = {'title': results['title'],
                                         'url': results['url']}
                        results_data.append(results_entry)

        else:
            raw_results_dict = results.json()
            results_list = raw_results_dict['results']

        # Create a List of Dictionaries for Each Result
        for results_dict in results_list:
            results_entry = {'title': results_dict['title'],
                             'url': results_dict['url']}
            results_data.append(results_entry)

    # Result Results Data
    return results_data, list_of_raw_results, previous_server


# Store Results in SQL Function
def store_results(args, database_name, database_file, results_data):

    # Database File Creation
    if not database_file:
        if not os.path.exists('./' + database_name):
            os.mknod(database_name)
            database_file = os.getcwd() + '/' + database_name

    # Create Database Connection and Cursor
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()

    # Check if Database Table Exists
    table_exists = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='search_results';").fetchall()

    # If Database Table Does Not Exist Create it
    if table_exists == []:
        cursor.execute(
                "CREATE TABLE search_results (query TEXT, title TEXT, url TEXT)")

    # If Merge Database
    if args.mergedatabase:
        # Insert Data into Database
        for entry in results_data:
            cursor.execute(
                    "INSERT INTO search_results VALUES (?, ?, ?);",
                    (entry[0], entry[1], entry[2]))

    else:
        # Insert Data into Database
        for entry in results_data:
            cursor.execute(
                    "INSERT INTO search_results VALUES (?, ?, ?);",
                    (args.query, entry['title'], entry['url']))

    # Deduplicate SQL Entries
    cursor.execute("CREATE TABLE temp_table as SELECT DISTINCT * FROM search_results;")
    cursor.execute("DELETE FROM search_results;")
    cursor.execute("INSERT INTO search_results SELECT * FROM temp_table ORDER BY query")
    cursor.execute("DROP TABLE temp_table;")

    # Commit Database Entries
    connection.commit()

    # Query Data from Database
    database_results = cursor.execute(
            'SELECT title, url FROM search_results').fetchall()

    # Close Database Connection
    connection.close()

    # Return Database Entries
    return database_results


# Output Function
def output_results(args, concurrent_connections,
                   results, list_of_raw_results,
                   database_results, previous_results,
                   total_current_results):

    # Initialize Local Current Results Variable
    current_results = []

    # Create Formated List of Current Results
    for result in database_results:
        current_result = "{} | {}".format(result[0], result[1])
        current_results.append(current_result)

    # Pretty Print Raw JSON Reponses in Very Verbose Mode for Single Page Mode
    if not concurrent_connections and args.veryverbose is True:

        # Print Raw Search Results to STDOUT
        pprint.pprint(results[0].json())

    # Pretty Print Raw JSON Reponses in Very Verbose Mode for Concurrent Page Mode
    elif concurrent_connections > 0 and args.veryverbose is True:
        pprint.pprint(list_of_raw_results)

    # Print New Results
    elif args.veryverbose is False or previous_results != total_current_results or previous_results == []:

        for result in current_results:
            if result not in total_current_results:
                print(result)
                total_current_results.append(result)

    return previous_results, total_current_results
