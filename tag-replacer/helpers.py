import requests
import re

DASHBOARD_EXTRA_CONFIGS = [
    "author_name",
    "author_handle",
    "id",
    "url",
    "created_at",
    "modified_at"
]

MONITOR_EXTRA_CONFIGS = [
    "deleted",
    "matching_downtimes",
    "id",
    "multi",
    "created",
    "created_at",
    "creator",
    "org_id",
    "modified",
    "overall_state_modified",
    "overall_state"
]

SYNTHETIC_EXTRA_CONFIGS = [
    "public_id",
    "monitor_id",
]


def call_api(request_path, dd_api_key, dd_app_key, eu_customer=False, method="GET", body=None):
    """Helper function used to call the DD API

    :param string request_path: the endpoint that we are calling from the Datadog API
    :param string dd_api_key: Datadog api key used to authenticate to API
    :param string dd_app_key: Datadog app key used to authenticate to API
    :param boolean eu_customer: True if customer is in EU, otherwise false
    :param string method: the method we are using when calling API
    :param dict body: the body of the request if we are updating/creating a value via API
    :return: json of request made
    """
    headers = {
        "content-type": "application/json",
        "DD-API-KEY": dd_api_key,
        "DD-APPLICATION-KEY": dd_app_key
    }

    # EU costumers need to define 'api_host' as below
    if eu_customer == "True":
        headers["api_host"] = "https://api.datadoghq.eu/"

    try:
        if method.upper() == "GET":
            # Make DD API GET request
            results = requests.get(
                "https://api.datadoghq.com/api/v1/" + request_path,
                headers=headers
                # params=api_params
            )
        elif method.upper() == "PUT":
            if body is None:
                raise Exception("A valid body is required to make a PUT request. Please try again")

            # Make DD API request
            results = requests.put(
                "https://api.datadoghq.com/api/v1/" + request_path,
                headers=headers,
                json=body
            )
        else:
            raise Exception("Unsupported API Call type.")

        # Raise an error if there was one
        results.raise_for_status()
        # If call is successful, return json result
        return results.json()
    except requests.exceptions.HTTPError as e:
        raise Exception("Non-200 response code returned from DD API: {}").with_traceback(e.__traceback__)


def get_metric_query(query, requests_object):
    """Parses a query/requests object and provides the actual Datadog query

    :param query: String or Dict, contains query from datadog
    :param dict requests_object: Contains the request object from datadog (has all queries)
    :return: The parsed individual query from datadog
    """
    if not query:
        return query

    if type(query) is str:
        if query == "x" or query == "y" or query == "fill" or query == "size":
            # Query equals either "x" or "y"
            metric_query = requests_object[query]["q"]
        else:
            raise Exception("Unsupported string query. Please add it in.")
    elif "process_query" in query:
        metric_query = query["process_query"]["filter_by"]
    elif query["q"]:
        metric_query = query["q"]
    else:
        raise Exception("Query type not supported")

    return metric_query


def build_new_request(new_metric_query, query, requests_object, index_counter):
    """Builds an updated request object with the query containing the new tags

    :param string new_metric_query: the metric query containing the new tags
    :param query: String/Dict containing the current query
    :param dict requests_object: the original request from dd API
    :param int index_counter: the index of which this item comes from if it's from an array
    :return: the updated request response to replace the original
    """
    if not query:
        return query

    if type(query) is str:
        if query == "x" or query == "y" or query == "fill" or query == "size":
            requests_object[query]["q"] = new_metric_query
        else:
            raise Exception("Unsupported string query. Please add it in.")

    elif "process_query" in query:
        requests_object[index_counter]["process_query"]["filter_by"] = new_metric_query
    elif requests_object[index_counter]["q"]:
        requests_object[index_counter]['q'] = new_metric_query
    else:
        raise Exception("Query type is not currently supported.")

    return requests_object


def find_and_replace_tags(metric_query, tags):
    """Goes through every tag and replaces the old one (if present) with the new

    :param string metric_query: the query for which we need to update for the widget
    :param dict tags: dict where key is a key:value pair for the old tag and the value is a key:value pair of new tag
    :return: updated metric query
    """
    replace_tracker = False
    for current_tag, new_tag in tags.items():
        if current_tag in metric_query:
            if type(metric_query) == list:
                metric_query, temp_replace_tracker = replace_all(metric_query, current_tag, new_tag)

                if not replace_tracker and temp_replace_tracker:
                    replace_tracker = True
            else:
                metric_query, replace_counter = re.subn(r'\b' + current_tag + r'\b', new_tag, metric_query)
                if not replace_tracker and replace_counter > 0:
                    replace_tracker = True

    return metric_query, replace_tracker


def replace_all(original_list, current_tag, new_tag):
    """Helper function that runs regex replace on a list and creates a new list

    :param list original_list: the original list that has the items to be replace
    :param string current_tag: the current string tag we want to replace
    :param string new_tag: the new item we want to replace the list items with
    :returns: updated list with the new items
    """
    replace_tracker = False

    for index, current_string in enumerate(original_list):
        if current_tag == current_string:
            original_list[index], replace_counter = re.subn(r'\b' + current_tag + r'\b', new_tag, current_string)

            if not replace_tracker and replace_counter > 0:
                replace_tracker = True

    return original_list, replace_tracker


def cleanup_dashboard_json(dashboard_config):
    """Helper function that removes non-required/invalid json values from dashboard config

    :param dashboard_config: Json of a datadog dashboard
    :return: Updated Json of a datadog dashboard
    """

    for json_key in DASHBOARD_EXTRA_CONFIGS:
        try:
            del dashboard_config[json_key]
        except KeyError:
            pass

    return dashboard_config


def cleanup_monitor_json(monitor_config):
    """Helper function that removes non-required/invalid json values from monitor config

    :param monitor_config: Json of a monitor config
    :return: Updated Json of a monitor config
    """

    for json_key in MONITOR_EXTRA_CONFIGS:
        try:
            del monitor_config[json_key]
        except KeyError:
            pass

    return monitor_config


def cleanup_synthetic_json(synthetic_config):
    """Helper function that removes non-required/invalid json values from synthetic config

    :param synthetic_config: Json of a synthetic config
    :return: Updated Json of a synthetic config
    """

    for json_key in SYNTHETIC_EXTRA_CONFIGS:
        try:
            del synthetic_config[json_key]
        except KeyError:
            pass

    return synthetic_config
