#!/usr/bin/env python3
# Script to pull all hosts from Datadog API and creates a csv file with the hosts and their tags

import requests, sys, json, datetime, csv
CSV_HEADERS = ["name", "id","RD_Status", "RD_Notes", "Replacement_Monitor", "Final_Status", "tags", "type", "creator_email", "priority", "query"]
CSV_DATA = []

DD_API_KEY = ""
DD_APP_KEY = ""

def get_monitors(filters=None):
    """API helper function for calling the Datadog API endpoint
    
    :returns: host request
    """

    # Build the headers for the request
    headers = {
        "DD_SITE":"datadoghq.com",
        "DD-API-KEY": DD_API_KEY, 
        "DD-APPLICATION-KEY": DD_APP_KEY
        }

    # Build the params for the request
    params = {
        "filter": filters
        }

    # Try to make the request, raise exception if it fails
    try:
        return requests.get("https://api.datadoghq.com/api/v1/monitor", headers=headers, params=params).json()
    except Exception as e:
        raise Exception("Error when getting monitors from api: {}".format(e))


def build_monitors(response):
    """ Pass in a json object with optional tag value from stdin and an optional header flag to check if it is for creating a new csv."""
        
    for monitor in response:
        # Get all the properties of this host
        name = monitor.get("name", "")
        id = monitor.get("id", "")
        query = monitor.get("query", "")
        priority = monitor.get("priority")
        tags = monitor.get("tags", [])
        type = monitor.get("type", "")
        creator_handle = monitor.get("creator", {}).get("handle", "")

        # Build the row of data
        monitor_info_row = [name, id, "TODO", "", "", "", tags, type, creator_handle, priority, query]
  
        # Append it to our list of data
        CSV_DATA.append(monitor_info_row)

# Main function to call api, create new file, write to new file, and save as .csv
def main():
    # Get current time
    time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Initialize tag argument variable
    tag_arg = None
    
    # Get the argument from the command line if available
    try:
        tag_arg = sys.argv[1]
    except IndexError: # No argument passed in
        pass


    # Make call out to get the hosts
    monitors_response = get_monitors(filters=tag_arg)

    # Get total number of hosts returned by the API
    monitor_count = len(monitors_response)
    
    if not monitors_response or monitor_count == 0:
        raise Exception("No hosts returned with the query. Please validate that your API/APP key are correct and the query returns hosts via the UI.")

    
    # Build the CSV list data
    build_monitors(monitors_response)

    # Print total number of hosts we are getting through
    print(f"Total monitors to report from API: {monitor_count}")

    with open(f"monitor_list_{time}.csv", mode='w') as monitor_list_file:
        monitor_writer = csv.writer(monitor_list_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        monitor_writer.writerow(CSV_HEADERS)

        for monitor in CSV_DATA:
            monitor_writer.writerow(monitor)
        
if __name__ == '__main__':
    main()
