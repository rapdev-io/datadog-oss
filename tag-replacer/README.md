# RapDev Tag Replacer

## Introduction

The goal of the tag replacer is to assist teams with auditing and compliance of datadog tags across their dashboards, monitors, and synthetics. 
It works by searching through all (or specified) resources in the provided datadog account and replacing the existing specified tags in queries and tag sections
with newly specified tags. 

## Pre-reqs

- [Python3.x Environment](https://realpython.com/installing-python/#how-to-install-python-on-macos)
- [Python DotEnv Library](https://pypi.org/project/python-dotenv/)
- [Python Requests Library](https://pypi.org/project/requests/)

## Configuration

### Environment File

Begin by providing a `.env` in the same directory you are running the `replacer.py` from. The `.env` file should contain the following information:
    
    DD_API_KEY="<YOUR_API_KEY>"
    DD_APP_KEY="<YOUR_APP_KEY>"
    EU_CUSTOMER=False
    RUN_MODE=test # Options are: prod/test
    

Please set the `EU_CUSTOMER` to `True` if you are a European Datadog customer otherwise leave it as `False`.

**NOTE:** For the `RUN_MODE` param, setting it to `test` will not make any changes in your account but print out what resources will be changed.
It is recommended that you run the first iteration in test mode to see the effect that the script will have in your account. If you feel the changes
to be made are accurate, then run it in `prod` mode to update your datadog account. 

### JSON File

The second part of configurations required is providing a `configs.json` file also within the same directory as `replacer.py`. The `configs.json` file
contains the following:
 - Old tag as the key with the new tag as the values (Required)
 - List of Dashboard IDs to target (Optional)
 - List of Monitor IDs to target (Optional)
 - List of Synthetic IDs to target (Optional)

If you provide an EMPTY LIST for the Dashboard/Monitors/Synthetics tag value, it will ignore that category altogether. For example,
having the configuration below will ONLY run the tag replacer script on the dashboard "xyu-rz9-kan":

    {
      "tags": {
        "test:mytestvalue": "newtest:newtestvalue"
      },
      "dashboards": [
        "xyu-rz9-kan"
      ],
      "monitors": [],
      "synthetics": []
    }

If you pass in a wildcard (e.g. "*") for any of the configs, it will target all specific resources.  

If you don't provide the IDs for the Dashboards/Monitors/Synthetics it will target every resource respectively. 
Here is what a VALID config.json looks like that targets 1 dashboard, 2 monitors, and 1 synthetic:
    
    {
      "tags": {
        "test:mytestvalue": "newtest:newtestvalue",
        "test1:mytestvalue1": "newtest1:newtestvalue1",
        "test2:mytestvalue2": "newtest2:newtestvalue2",
        "test3:mytestvalue3": "newtest3:newtestvalue3"
      },
      "dashboards": [
        "xyu-rz9-kan"
      ],
      "monitors": [
        36302563,
        36302732
      ],
      "synthetics": [
        "huf-wgd-esx"
      ]
    }

For reference, the tags section above is saying replace the tag key/value pair `test:mytestvalue` with the new tag key/value pair `newtest:newtestvalue`.

**NOTE**: If you wanted to target every resource of one type, remove the entire respective section including the key (e.g. "dashboards"/"monitors"/"synthetics"). For example, this configuration targets every resource:
    
    {
      "tags": {
        "test:mytestvalue": "newtest:newtestvalue",
        "test1:mytestvalue1": "newtest1:newtestvalue1",
        "test2:mytestvalue2": "newtest2:newtestvalue2",
        "test3:mytestvalue3": "newtest3:newtestvalue3"
      }
    }

## Running the Script

Using your `python3.X` command (make sure you use your installed version), you can run the script in one simple command from within the directory:

    # Only run one of these based on your python version:

    python3 replacer.py
    python3.7 replacer.py
    python3.8 replacer.py
    
    
## Warnings
This script is only meant to be used to replace an old tag key/value pair with a new one. It does NOT work well with removing tags altogether. Please don't try to provide an old value and map it to an empty value as it could break things in your account. For example, do not do the following:
    
    "tags": {
      "test:test1": ""
    }
