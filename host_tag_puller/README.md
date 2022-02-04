# RapDev Tag + Key Puller

## Introduction

The goal of the tag puller is to assist teams with auditing all of the Datadog tags across their hosts in their Datadog instance. 
It works by searching through all hosts in the provided Datadog account and generating a report with a list of all tags in the datadog account. 

## Pre-reqs

- [Python3.x Environment](https://realpython.com/installing-python/)

You will need to install the following Python librarys:

- [Datadog Python library](https://datadogpy.readthedocs.io/en/latest/)
- [python-dotenv Library](https://pypi.org/project/python-dotenv/)


## Configuration

### Environment File

Begin by providing a `.env` in the same directory you are running the `host_tag.py` from. The `.env` file should contain the following information:
    
    DD_API_KEY="<YOUR_API_KEY>"
    DD_APP_KEY="<YOUR_APP_KEY>"
    DD_CUSTOMER="<NAME_FOR_GENERATED_REPORT>"

Provided in the repository is a skeleton `.env.template` that can be renamed to `.env` with the appropriate keys and configurations.
## Running the Script

Using your `python3.X` command (make sure you use your installed version), you can run the script in one simple command from within the directory:

    # Only run one of these based on your python version:

    python3 host_tag.py
    python3.7 host_tag.py
    python3.8 host_tag.py
    python3.9 host_tag.py
    