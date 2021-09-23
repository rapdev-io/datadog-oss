# RapDev Host List CSV Generator

## Before Running:

Python 3.8+ is required to run. 

After installing and updating Python:  
Run in terminal:  

`python3 -m pip install -r requirements.txt`  

This will install the `requests` package for making API calls.  

## To Run:

The script is called `rapdev_list_host.py`. To run, entire in your terminal:  

`python3 rapdev_list_host.py <SEARCH>`  where \<SEARCH> is replaced with an optional search term. This can be a Datadog tag or Datadog-provided attribute. No quotes are necessary. If ran without a search term, the script will pull every active host. You may add multiple tags or attributes but separating them with a comma (no spaces). For example:  

`python3 rapdev_list_host.py field:metadata_agent_version:noagent,env:prod`  

Which would create a .csv file called `host_list_<CURRENTTIME>.csv` with a header `host_name, ip, sources, tags` and rows with the data pulled from Datadog.

You will notice that the above example will not result in any lines written to a csv. That is because this script will return hosts that currently have a Datadog Agent installed on them. The script is able to handle hosts with **and** without agents.  
If desired, the script can be changed to allow for returning hosts without agents if edited directly. The default value can be directly changed on the `agent_only` argument in the method `filter_hosts()` (it is on line 26 column 61) by changing the `1` to a `0`. If changed, the script will pull all hosts including vsphere, azure, etc.