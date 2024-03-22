# Datadog Duplicate Host Checker

This Python script is designed to help identify duplicate hosts in Datadog, focusing on the comparison between FQDN (Fully Qualified Domain Name) and Non-FQDN hosts. It uses the Datadog API to fetch hosts based on an optional tag argument and checks for duplicates, helping to maintain cleaner host records in your Datadog account.

## Prerequisites
Before using this script, ensure you have:
- Python 3.x installed.
- Access to the Datadog API with valid API and Application keys.
- The requests and pandas Python libraries installed.

## Setup
1. Clone or download this script to your local machine.
2. Install the required Python libraries by running:
  ```
  pip install requests pandas
  ```

3. Update the script with your Datadog API and Application keys:
  ```
  DD_API_KEY = "your_datadog_api_key"
  DD_APP_KEY = "your_datadog_app_key"
  ```

  You can find these keys in your Datadog account under Integrations > APIs.

4. Run the script from the command line, optionally passing a tag to filter the hosts:
```
python duplicate_host_checker.py [optional_tag]
```

## How It Works
The script makes a request to Datadog's Hosts API endpoint, retrieves hosts based on the provided tag (if any), and analyzes the data to identify duplicates based on FQDN vs Non-FQDN comparisons. The results are then saved to a CSV file, detailing the identified duplicate hosts.

## Output
A CSV file named dd_fqdn_duplicates_<timestamp>.csv will be generated in the directory from which the script was run. This file lists the duplicate host names identified by the script.
