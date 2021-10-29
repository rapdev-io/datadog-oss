import requests
import os
import json
import helpers
from dotenv import load_dotenv

UNSUPPORTED_TYPES = {
    "alert_value",
    "check_status",
    "alert_graph",
    "slo",
    "image",
    "trace_service",
    "free_text",
    "iframe"
}


def update_dashboards(dd_api_key, dd_app_key, eu_customer, tags, config_dashboard_list=None):
    """Updates all the dashboard in a DD account based on tags provided

    :param string dd_api_key: Datadog api key used to authenticate to dashboard endpoint
    :param string dd_app_key: Datadog app key used to authenticate to dashboard endpoint
    :param boolean eu_customer: True if customer is in EU, else false
    :param dict tags: contains key/value of the old tags/new tags to replace
    :param list config_dashboard_list: contains dashboard ids to only target (targets all if None)
    :return:
    """
    dashboards_list = helpers.call_api("dashboard", dd_api_key, dd_app_key, eu_customer)["dashboards"]

    TEST_MODE_SET = set()

    for dashboard in dashboards_list:
        dashboard_id = dashboard["id"]
        if config_dashboard_list and dashboard_id not in config_dashboard_list:
            continue

        final_replace_tracker = False

        # Get the config for the dashboard using the id returned in original call
        dashboard_config = helpers.call_api(
            "dashboard/{}".format(dashboard_id),
            dd_api_key,
            dd_app_key,
            eu_customer
        )
        widgets = dashboard_config["widgets"]

        for widget_counter, widget in enumerate(widgets):
            # Response: {'definition': {'requests': [{'q':...}] OR [{'q':...}, {'q':...}, etc...] }}
            if widget["definition"].get("requests"):
                requests_object = widget["definition"].get("requests")

                for query_counter, query in enumerate(requests_object):
                    # Ignore the following queries: logs, apm, network, and rum
                    if ("log_query" in query) or ("apm_query" in query) \
                            or ("rum_query" in query) or ("network_query" in query):
                        continue

                    metric_query = helpers.get_metric_query(query, requests_object)
                    new_metric_query, replace_tracker = helpers.find_and_replace_tags(metric_query, tags)

                    # Update tracker value if it hasn't already been updated
                    if replace_tracker and not final_replace_tracker:
                        final_replace_tracker = True

                    requests_object = helpers.build_new_request(new_metric_query, query,
                                                                requests_object, query_counter)

                    # TODO: Handle 'metadata':[{...,'expression': "<query>" ]}
                widgets[widget_counter]["definition"]["requests"] = requests_object

            # Response: {'definition': {'widgets': [{'definition':..., 'requests': [{'q':...}] }] }}
            elif widget["definition"].get("widgets"):
                definitions = widget["definition"].get("widgets")

                for definition_counter, definition in enumerate(definitions):
                    # Check if widget definition has a request in it
                    if definition["definition"].get("requests"):
                        requests_object = definition["definition"].get("requests")

                        for query_counter, query in enumerate(requests_object):
                            # Ignore the following queries: logs, apm, network, and rum
                            if ("log_query" in query) or ("apm_query" in query) \
                                    or ("rum_query" in query) or ("network_query" in query):
                                continue
                            metric_query = helpers.get_metric_query(query, requests_object)
                            new_metric_query, replace_tracker = helpers.find_and_replace_tags(metric_query, tags)
                            requests_object = helpers.build_new_request(new_metric_query, query,
                                                                        requests_object, query_counter)

                            if replace_tracker and not final_replace_tracker:
                                final_replace_tracker = True

                        widgets[widget_counter]["definition"]["widgets"][definition_counter]["definition"]["requests"] = requests_object
            # Response: {'definition': {'query':..., }}
            elif widget["definition"].get("query"):
                widgets[widget_counter]["definition"]["query"], replace_tracker = \
                    helpers.find_and_replace_tags(widget["definition"].get("query"), tags)

                if replace_tracker and not final_replace_tracker:
                    final_replace_tracker = True

            # Response: {'definition': {'filters':..., }}
            elif widget["definition"].get("filters"):
                widgets[widget_counter]["definition"]["filters"], replace_tracker = \
                    helpers.find_and_replace_tags(widget["definition"].get("filters"), tags)

                if replace_tracker and not final_replace_tracker:
                    final_replace_tracker = True

            elif widget["definition"].get("type") in UNSUPPORTED_TYPES:
                # Unsupported Query
                pass
            else:
                # print("Unparsed calls: ", widget)
                pass

        # Update dashboard config's widgets
        dashboard_config["widgets"] = widgets

        if final_replace_tracker:
            if RUN_MODE == "prod":
                # Clean up JSON body
                dashboard_config = helpers.cleanup_dashboard_json(dashboard_config)

                # Update existing dashboard with new config
                helpers.call_api(
                    "dashboard/{}".format(dashboard_id),
                    dd_api_key,
                    dd_app_key,
                    eu_customer,
                    "PUT",
                    dashboard_config
                )
            elif RUN_MODE == "test":
                TEST_MODE_SET.add(dashboard_id)
        else:
            pass

    if RUN_MODE == "test":
        print("** DASHBOARDS **")
        print("Script will update {} dashboard(s).".format(len(TEST_MODE_SET)))
        print(*TEST_MODE_SET, sep=", ")


def update_monitors(dd_api_key, dd_app_key, eu_customer, tags, config_monitor_list=None):
    """Updates all the monitors in a DD account based on tags provided

    :param string dd_api_key: Datadog api key used to authenticate to monitor endpoint
    :param string dd_app_key: Datadog app key used to authenticate to monitor endpoint
    :param boolean eu_customer: True if customer is in EU, else false
    :return:
    """
    monitors_list = helpers.call_api("monitor", dd_api_key, dd_app_key, eu_customer)

    TEST_MODE_SET = set()

    for monitor in monitors_list:
        monitor_id = monitor["id"]

        final_replace_tracker = False

        # If monitor list is specified only continue with loop if ID is present in the list
        if config_monitor_list and monitor_id not in config_monitor_list:
            continue

        # Grab the query from monitor response and replace accordingly
        monitor_query = monitor["query"]
        if monitor_query:
            monitor["query"], replace_tracker = helpers.find_and_replace_tags(monitor_query, tags)

            if replace_tracker and not final_replace_tracker:
                final_replace_tracker = True

        # Grab the tags from monitor response and replace accordingly
        monitor_tags = monitor["tags"]
        if monitor_tags:
            monitor["tags"], replace_tracker = helpers.find_and_replace_tags(monitor_tags, tags)

            if replace_tracker and not final_replace_tracker:
                final_replace_tracker = True

        # Update existing monitor with new config(s)
        if final_replace_tracker:
            if RUN_MODE == "prod":
                # Clean up JSON body
                monitor = helpers.cleanup_monitor_json(monitor)
                helpers.call_api(
                    "monitor/{}".format(monitor_id),
                    dd_api_key,
                    dd_app_key,
                    eu_customer,
                    "PUT",
                    monitor
                )
            elif RUN_MODE == "test":
                TEST_MODE_SET.add(monitor_id)
        else:
            pass


    if RUN_MODE == "test":
        print("** MONITORS **")
        print("Script will update {} monitor(s).".format(len(TEST_MODE_SET)))
        print(*TEST_MODE_SET, sep=", ")

def update_synthetics(dd_api_key, dd_app_key, eu_customer, tags, config_synthetic_list=None):
    """Updates all the synthetics in a DD account based on tags provided

    :param string dd_api_key: Datadog api key used to authenticate to synthetics endpoint
    :param string dd_app_key: Datadog app key used to authenticate to synthetics endpoint
    :param boolean eu_customer: True if customer is in EU, else false
    :return:
    """
    synthetics_list = helpers.call_api("synthetics/tests", dd_api_key, dd_app_key, eu_customer)["tests"]

    TEST_MODE_SET = set()

    for synthetic in synthetics_list:
        synthetic_id = synthetic["public_id"]

        # If synthetic list is specified only continue with loop if ID is present in the list
        if config_synthetic_list and synthetic_id not in config_synthetic_list:
            continue

        # Grab type to determine API call path
        synthetic_type = synthetic["type"]

        # Build path using synthetic type
        if synthetic_type == "browser":
            path = "synthetics/tests/browser/{}".format(synthetic_id)
        elif synthetic_type == "api":
            path = "synthetics/tests/api/{}".format(synthetic_id)

        # Get entire config for the synthetic
        synthetic_config = helpers.call_api(path, dd_api_key,dd_app_key, eu_customer)

        # Get tags field from synthetic response
        synthetic_tags = synthetic_config["tags"]
        synthetic_config["tags"], final_replace_tracker = helpers.find_and_replace_tags(synthetic_tags, tags)

        if final_replace_tracker:
            if RUN_MODE == "prod":
                # Cleanup synthetic config
                synthetic_config = helpers.cleanup_synthetic_json(synthetic_config)

                helpers.call_api(
                    path,
                    dd_api_key,
                    dd_app_key,
                    eu_customer,
                    "PUT",
                    synthetic_config
                )
            elif RUN_MODE == "test":
                TEST_MODE_SET.add(synthetic_id)
        else:
            pass

    if RUN_MODE == "test":
        print("** SYNTHETICS **")
        print("Script will update {} synthetic(s).".format(len(TEST_MODE_SET)))
        print(*TEST_MODE_SET, sep=", ")


def main():
    if "DD_API_KEY" in os.environ and "DD_APP_KEY" in os.environ:
        dd_api_key = os.environ.get('DD_API_KEY')
        dd_app_key = os.environ.get('DD_APP_KEY')
    else:
        raise Exception("Datadog API and APP keys are required. Please provide both via environment variables.")

    eu_customer = os.environ.get('EU_CUSTOMER', False)

    # Open JSON file with configs
    with open('configs.json') as f:
        json_file = json.load(f)

    try:
        # Grab the tags in the json file
        tags = json_file["tags"]
    except KeyError as e:
        raise Exception("Tags field is required in the tags json. Please make sure it's specified and run again.")

    # Dashboards
    dashboards = json_file.get("dashboards")
    if dashboards is not None and len(dashboards) == 0:
        print("Ignoring dashboards due to configs.json empty dashboards list.")
    elif dashboards and "*" not in dashboards:
        dashboards = set(dashboards)
        update_dashboards(dd_api_key, dd_app_key, eu_customer, tags, dashboards)
    else:
        # If "dashboards" is not set or dashboards is set to ["*"], run function on all dashboards
        update_dashboards(dd_api_key, dd_app_key, eu_customer, tags)

    # Monitors
    monitors = json_file.get("monitors")
    if monitors is not None and len(monitors) == 0:
        print("Ignoring monitors due to configs.json empty monitors list.")
    elif monitors and "*" not in monitors:
        monitors = set(monitors)
        update_monitors(dd_api_key, dd_app_key, eu_customer, tags, monitors)
    else:
        update_monitors(dd_api_key, dd_app_key, eu_customer, tags)

    # Synthetics
    synthetics = json_file.get("synthetics")
    if synthetics is not None and len(synthetics) == 0:
        print("Ignoring synthetics due to configs.json empty synthetics list.")
    elif synthetics and "*" not in synthetics:
        synthetics = set(synthetics)
        update_synthetics(dd_api_key, dd_app_key, eu_customer, tags, synthetics)
    else:
        update_synthetics(dd_api_key, dd_app_key, eu_customer, tags)

if __name__ == '__main__':
    # loads environment variables
    load_dotenv()
    # Get run mode, if not set defaults to test
    global RUN_MODE
    RUN_MODE = os.environ.get("RUN_MODE", "test")

    main()
