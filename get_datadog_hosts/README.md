# RapDev Host List CSV Generator

## Before Running:

Python 3.8+ is required to run. 

After installing and updating Python:  
Run in terminal:  

`python3 -m pip install -r requirements.txt`  

This will install the following packages:

    ```
    certifi==2021.5.30
    charset-normalizer==2.0.6
    distlib==0.3.2
    idna==3.2
    requests==2.26.0
    urllib3==1.26.6
    ```

## To Run:

The script is called `list_datadog_hosts.py`. To run, entire in your terminal:  

`python3 rapdev_list_host.py <SEARCH>`  where `<SEARCH>` is replaced with an optional search term or left empty. This can be a Datadog tag or Datadog-provided attribute. No quotes are necessary. If ran without a search term, the script will pull every active host. You may add multiple tags or attributes but separating them with a comma (no spaces). 

### Examples

- Get all hosts without agents on Azure:

    ```
    python3 list_datadog_hosts.py field:metadata_agent_version:noagent,field:apps:azure
    ```

- Get all hosts without agents on AWS:

    ```
    python3 list_datadog_hosts.py field:metadata_agent_version:noagent,field:apps:aws
    ```

- Get all hosts with agents:

    ```
    python3 list_datadog_hosts.py field:apps:agent
    ```

Running the command will create a .csv file called `host_list_<CURRENTTIME>.csv` with a header `host_name, ip, sources, tags` and rows with the data pulled from Datadog.
