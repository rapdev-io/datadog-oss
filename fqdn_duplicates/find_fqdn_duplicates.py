"""
This helper script takes two inputs; an excel sheet with a list of target hosts and a txt file with the output of an ansible tasks.
It compares the two and tries to find missing hosts in the output task so it's easy to find any hosts that stalled out with no clear error.
"""

import requests, sys, json, datetime, csv
import pandas as pd

my_hosts = []
datadog_hosts = []


CSV_HEADERS = ["host_name", "host_aliases", "os_info", "build_info", "host_apps", "sources", "last_reported_time", "host_status", "tags", "ipaddress"]
CSV_DATA = []

DD_API_KEY = ""
DD_APP_KEY = ""
DD_SITE = "api.datadoghq.com"

def get_hosts(filters=None, start=None, count=1000, include_muted_hosts_data=0, include_hosts_metadata=1):
    """API helper function for calling the Datadog API endpoint
    
    :returns: host request
    """

    # Build the headers for the request
    headers = {
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
        return requests.get(f"https://{DD_SITE}/api/v1/hosts", headers=headers, params=params).json()
    except Exception as e:
        raise Exception("Error when getting hosts from api: {}".format(e))


def build_hosts(response):
    """ Pass in a json object with optional tag value from stdin and an optional header flag to check if it is for creating a new csv."""
        
    for host in response.get("host_list", []):
        # Get all the properties of this host
        host_name = host.get("host_name", "")
        host_aliases = host.get("aliases", "")
        host_apps = host.get("apps", "")
        sources = host.get("sources", "")
        last_reported_time = host.get("last_reported_time", "")
        host_status = host.get("up", "")
        tags = host.get("tags_by_source", [])
        host_name = host_name.split(".")[0]

        datadog_hosts.append(host_name.lower())

        # Get ip address from meta > gohai > network > ipaddress if available
        meta = host.get("meta", {})
        gohai = json.loads(meta.get("gohai", "{}"))
        network = gohai.get("network", {})
        if network:
            ip_address = network.get("ipaddress", "")
        else:
            ip_address = ""

        windows_os_info = meta.get("winV", [])
        mac_os_info = meta.get("macV", [])

        if windows_os_info:
            os_info = windows_os_info[0]
            build_info = windows_os_info[1]
        elif mac_os_info:
            os_info = mac_os_info[0]
            build_info = mac_os_info[1]
        else:
            os_info = "N/A"
            build_info = "N/A"

        # Build the row of data
        host_info_row = [host_name, host_aliases, os_info, build_info, host_apps, sources, last_reported_time, host_status, tags, ip_address]

        # Append it to our list of data
        CSV_DATA.append(host_info_row)

def read_excel_hosts(excel_path):
    # Read Excel file
    df = pd.read_excel(excel_path)
    # Filter hosts based on pattern
    return [host.split('.')[0] for host in df[df.columns[0]]]


def find_duplicates(hostnames):
    # Dictionary to store base hostname and its variants
    host_dict = {}

    for hostname in hostnames:
        # Convert to lowercase
        hostname_lower = hostname.lower()

        # Split hostname and get the base part
        base_hostname = hostname_lower.split('.')[0]

        # Add to dictionary
        if base_hostname not in host_dict:
            host_dict[base_hostname] = [hostname_lower]
        else:
            host_dict[base_hostname].append(hostname_lower)

    # Find duplicates
    duplicates = {base: variants for base, variants in host_dict.items() if len(variants) > 1}

    return duplicates

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
        
        if not host_count or host_count == 0:
            raise Exception("No hosts returned with the query. Please validate that your API/APP key are correct and the query returns hosts via the UI.")

        # Increment by count
        pagination_count += 1000

        # If pagination count is greater than total number of hosts, break out
        if pagination_count > host_count:
            break
    
    # Print total number of hosts we are getting through
    print(f"Total hosts to report from API: {host_count}")

    my_duplicates = find_duplicates(datadog_hosts)

    print(f"Count of duplicates: {len(my_duplicates)}")

    with open(f"dd_fqdn_duplicates_{time}.csv", mode='w') as host_list_file:
        host_writer = csv.writer(host_list_file, quotechar='"', quoting=csv.QUOTE_MINIMAL)
        host_writer.writerow(["host_name"])
        for base, variants in my_duplicates.items():
            host_writer.writerow([base])

        
if __name__ == '__main__':
    main()

