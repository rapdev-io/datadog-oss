#!/usr/bin/env python3
# Script to pull all hosts from Datadog API and creates a csv file with the hosts and their tags

import requests, sys, json, datetime, csv

CSV_HEADERS = ["host_name", "host_aliases", "host_apps", "sources", "last_reported_time", "host_status", "tags", "ipaddress"]
CSV_DATA = []

DD_API_KEY = ""
DD_APP_KEY = ""


def get_hosts(filters=None, start=None, count=1000, include_muted_hosts_data=0, include_hosts_metadata=1):
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
        "filter": filters,
        "start": start,
        "count": count
        }

    # Try to make the request, raise exception if it fails
    try:
        return requests.get("https://api.datadoghq.com/api/v1/hosts", headers=headers, params=params).json()
    except Exception as e:
        raise Exception("Error when getting hosts from api: {}".format(e))


def build_hosts(response):
    """ Pass in a json object with optional tag value from stdin and an optional header flag to check if it is for creating a new csv.

    :returns: string
    """    
    for host in response.get("host_list", []):
        # Get all the properties of this host
        host_name = host.get("host_name", "")
        host_aliases = host.get("aliases", "")
        host_apps = host.get("apps", "")
        sources = host.get("sources", "")
        last_reported_time = host.get("last_reported_time", "")
        host_status = host.get("up", "")
        tags = host.get("tags_by_source", [])

        # Get ip address from meta > gohai > network > ipaddress if available
        meta = host.get("meta", {})
        gohai = json.loads(meta.get("gohai", "{}"))
        network = gohai.get("network", {})
        if network:
            ip_address = network.get("ipaddress", "")
        else:
            ip_address = ""

        # Build the row of data
        host_info_row = [host_name, host_aliases, host_apps, sources, last_reported_time, host_status, tags, ip_address]

        # Append it to our list of data
        CSV_DATA.append(host_info_row)

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

    # Initialize pagination counter
    pagination_count = 0

    # Do-while in python
    while True:
        # Make call out to get the hosts
        hosts_response = get_hosts(filters=tag_arg, start=pagination_count)

        # Build the CSV list data
        build_hosts(hosts_response)

        # Get total number of hosts returned by the API
        host_count = hosts_response.get('total_matching')

        # Increment by count
        pagination_count += 1000

        # If pagination count is greater than total number of hosts, break out
        if pagination_count > host_count:
            break
    
    # Print total number of hosts we are getting through
    print(f"Total hosts to report from API: {host_count}")

    with open(f"host_list_{time}.csv", mode='w') as host_list_file:
        host_writer = csv.writer(host_list_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        host_writer.writerow(CSV_HEADERS)

        for host in CSV_DATA:
            host_writer.writerow(host)
        
if __name__ == '__main__':
    main()
