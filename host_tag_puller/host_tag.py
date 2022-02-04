from datadog import initialize, api
from dotenv import load_dotenv
import os

def get_tags(dd_api_key, dd_app_key,dd_customer,outpath):
    """Gets all tags in a DD account then outputs keys and tags (key:value pairs) to a flatfile
    
    :param string dd_api_key: Datadog api key used to authenticate to Host endpoint
    :param string dd_app_key: Datadog app key used to authenticate to Host endpoint
    :param boolean eu_customer: True if customer is in EU, else false
    :return:
    """
    options = {
        "api_key": dd_api_key,
        "app_key": dd_app_key
    }

    outdir = outpath
    customer = dd_customer

    # Initialize Datadog module for API usage
    initialize(**options)

    # Grabbing the hosts list
    total_hosts = api.Hosts.totals().get('total_active')

    # Find all tags in each host and put them in a single list
    total_tag_list=[]
    n = 0
    while n < total_hosts:
        response = api.Hosts.search(start=n, count=1000)
        for host in response.get("host_list",""):
            for tags in host.get("tags_by_source","").values():
                    total_tag_list.append(tags)
        n+=1000

    # Join all lists to single list
    total_tag_list = sum(total_tag_list,[])

    # Track each key and value to write to the report
    lines_seen = set()
    final_value_list = open("{}/{}_vals".format(outdir, customer), "w")
    for item in total_tag_list:
        if "host" in item:
            pass
        else:
            if item not in lines_seen:
                final_value_list.write(item + "\n")
                lines_seen.add(item)

    # Unzip key value pairs to pull just the keys
    file_key_list = open("{}/{}_keys".format(outdir, customer), "w")
    keys_seen = set()
    for item in lines_seen:
        if ":" in item:        
            key = item.split(":", 1)[0]
        else:
            key = item
        if key not in keys_seen:
            file_key_list.write(key + "\n")
            keys_seen.add(key)

    final_value_list.close()
    file_key_list.close()

def main():
    # Get environment variables from .env
    if "DD_API_KEY" in os.environ and "DD_APP_KEY" in os.environ:
        dd_api_key = os.environ.get('DD_API_KEY')
        dd_app_key = os.environ.get('DD_APP_KEY')
        dd_customer = os.environ.get('DD_CUSTOMER')
    else:
        raise Exception("Datadog API and APP keys are required. Please provide both via environment variables.")
    
    # Create output directory
    outpath = os.path.join(os.getcwd(),"out")
    if not os.path.exists(outpath):
        os.mkdir(outpath)

    # Pull tags and generate report
    get_tags(dd_api_key,dd_app_key, dd_customer,outpath)

if __name__ == '__main__':
    # loads environment variables
    load_dotenv()
    # Get run mode, if not set defaults to test
    global RUN_MODE
    RUN_MODE = os.environ.get("RUN_MODE", "test")

    main()