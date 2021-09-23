#!/usr/bin/env python3
# rapdev_list_host.py
# Script to pull all hosts from Datadog API and creates a csv file with the hosts, ip, sources, and their tags
import requests, sys,json, datetime

# API helper function for calling the Datadog API endpoint
def get_hosts(filters=None, sort_field=None, sort_dir=None, start=None, count=1000, from_date=None, include_muted_hosts_data=0, include_hosts_metadata=1):
    headers = {"DD_SITE":"datadoghq.com",
                   "DD-API-KEY": "<API KEY>", 
                   "DD-APPLICATION-KEY": "<APP KEY>"}
    params = {
        "filter": filters,
        "sort_field": sort_field,
        "sort_dir": sort_dir,
        "start": start,
        "count": count,
        "from": from_date,
        "include_muted_hosts_data" : include_muted_hosts_data,
        "include_hosts_metadata" : include_hosts_metadata
        }
    return requests.get("https://api.datadoghq.com/api/v1/hosts", headers=headers, params=params) 


# Pass in a json object with optional tag value from stdin and an optional header flag to check if it is for creating a new csv.
# Returns a string
def filter_hosts(response,tag=None,header_only=0,agent_only=1):
    text = ""
    try:
        # Check if function should only create header row
        if header_only == 1:
            text = 'host_name,ipaddress,sources'
            # If search filter was passed in, add to header for visibility
            if tag is not None:
                text += f",tags_with_search_term='{tag.replace(',', ';')}' "
            else: text += ',tags'
            return text
    except Exception as e:
        print("Exception occurred while processing header.")
        # Filter down the host name, ip, and tags and append them to return value, text
    for col in response['host_list']:
        try:
            if 'host_name' in col:
                
                # If ipaddress or host sources don't exist, leave columns empty
                ip = ''
                sources = ''
                # If this flag is set from the args, make sure that only hosts with Datadog agents are pulled.
                if agent_only == 1:
                    agent_flag = 0
                    # Check each source for agent.
                    for agent in col['sources']:
                        if agent == 'agent':
                            agent_flag = 1
                        # If there is not Datadog agent installed, skip this host.
                    if agent_flag == 0: continue
                try:
                    decoded = json.loads(col['meta']['gohai'])
                    ip = decoded['network']['ipaddress']
                except: 
                    pass # if ip field doesn't exist, catch the exception and keep going. 
                # Append row to text string in format "host_name, ipaddress, sources, tags"
                text += '\n' + f"{col['host_name']}"
                text += f',{ip}'
                sources = ';'.join(col['sources'])
                text += f',{sources}'
                for source in col['tags_by_source']:
                    tags = ';'.join(col['tags_by_source'][source])
                    text += f',{tags}'
        except Exception as e:
            print(f'Exception occurred while processing csv: {e}')
    return text

# Main function to call api, create new file, write to new file, and save as .csv
def main():
    time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    tag_arg = None
    try:
        # Get search argument
        tag_arg = sys.argv[1]
    except IndexError:
        pass # no argument passed
    try:
        response = get_hosts(filters=tag_arg,count=1).json()
    except Exception as e:
        print(f'Exception occured:{e}')
    total = response['total_matching']
    print(f"Total hosts to paginate through:{total}")
    try: 
        print("Writing file...")
        ftype = open(f"host_list_{time}.csv", 'w', encoding='utf-8')
        ftype.write(filter_hosts(response=response,tag=tag_arg,header_only=1))
        ftype.close()
    except Exception as e:
        print (f"Exception: {e}")
    # Keep track of number of paginations
    count = int(total/1000) + (total % 1000 > 0)
    for i in range(0,count):
        # Paginate through api endpoint
        print(f"Paginating: {i+1}/{count}")
        resp = get_hosts(filters=tag_arg, start=(i*1000)).json()
        try: 
            ftype = open(f"host_list_{time}.csv", 'a+', encoding='utf-8')
            ftype.write(filter_hosts(resp, tag_arg))
            ftype.close()
        except Exception as e:
            print (f"Exception: {e}")
    print("Done processing.")
        
if __name__ == '__main__':
    main()