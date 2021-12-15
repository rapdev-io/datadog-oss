try:
    from datadog_checks.base import AgentCheck, is_affirmative, ConfigurationError
except ImportError:
    from checks import AgentCheck
import re
import traceback
from requests import HTTPError
from pkg_resources import parse_version
try:
    from datadog_agent import get_config
except ImportError:
    def get_config(key):
        return ""

IGNORE_APPS = [
    "alb",
    "elb",
    "nlb",
    "rds"
]

API_URL_MAP = {
    "com": "api.datadoghq.com",
    "eu": "api.datadoghq.eu",
    "us3": "api.us3.datadoghq.com",
    "us5": "api.us5.datadoghq.com",
    "gov": "api.ddog-gov.com"
}

class ValidatorCheck(AgentCheck):
    """
    class inherits from AgentCheck class and handles everything regarding the checking of tags on hosts
    in your Datadog environment
    
    attribs:
        org (str): the name of the org (or parent_billing org if in a multi org env) associated with the
                   api key for the current instance
        ignore_hosts (list[str]): list of python regexes, pulled in from the conf.yaml, defining patterns
                                  for hostnames to ignore validation on
    """
    
    __NAMESPACE__ = "rapdev.validator"

    def __init__(self, *args, **kwargs):
        super(ValidatorCheck, self).__init__(*args, **kwargs)
        self.dd_site = self.instance.get("dd_site", "com")
        self.api_url = API_URL_MAP.get(self.dd_site)
        self.options = self.get_keys()
        self.check_initializations.append(self.validate_config) 
        self.org = self.get_org(self.options)


        self.ignore_hosts = set(self.instance.get("hosts_to_ignore", []))
        self.tags = self.instance.get("tags", [])

    def check(self, _):
        """
        main check loop grabs all of the hosts from the Datadog api, and iterates over them, checking the agent
        and tag information as it goes, and submits its findings to the Datadog api
        """

        self.tags = list(set(self.tags))
        self.tags.append("org:{}".format(self.org))

        self.log.debug("Attempting to grab the total number of active hosts from your Datadog account....")

        response = self.http.get("https://{}/api/v1/hosts/totals".format(self.api_url), extra_headers = self.options).json()
        total_hosts = response.get("total_active")
        
        n = 0
        count = 1000
        while n < total_hosts:
            response = self.http.get("https://{}/api/v1/hosts?start={}&count={}".format(self.api_url, n, count), extra_headers=self.options).json()
            host_list = response.get("host_list", [])
            for host in host_list:
                if not self.is_ignored_host(host.get("name")):
                    self.validate_agent(host)
                
                n += 1
        
    def get_keys(self):
        """
        function to retrieve the api and app key being used for the current instance
        
        notes:
            - first attempts to retrieve both the api key and app key from the current instance config
            - api key
                - if it is not specified for the current instance it then attempts to retrieve it from the
                  init_config section for the entire integration
                - if the api key is not found in the init_config section, it attempts to grab it from the main
                  datadog.yaml config
                - it should throw an exception at that point if it is still not able to find it, but if
                  it were to reach this point, it will throw a configuration error exception here
            - app key
                - if it is not specified for the current instance it then attempts to retrieve it from the
                  init_config section for the entire integration
                - if it is still not found it will then throw a configuration error exception
            - allowing the user to specify in the init_config section ensures backwards compatibility
              with previous versions of this integration
        
        returns:
            options (dict): dictionary containing the api key, and app key mapped to their proper name for
                            use with the Datadog python library, and its initialize function
                            
        raises:
            (datadog_checks.base.ConfigurationError): raises this exception if it is not able to determine either
                                                      the api key, or app key, for the current instance
        """
        api_key = self.instance.get("api_key", "") # default to instance based api key
        app_key = self.instance.get("app_key", "") # default to instance based app key
        
        # if no api key specified for instance, grab from init_config
        if not api_key:
            api_key = self.init_config.get("api_key", "")
            # if no api key specified for instance, grab from main datadog.yaml
            if not api_key:
                api_key = get_config("api_key")
                
                # if no api key found and somehow gets here, throw an exception
                # (it should not be able to get here with passthrough_exceptions set to False for get_config)
                if not api_key:
                    raise ConfigurationError("No api key found")
            
        # if no app key specfied for instance, grab from init_config
        if not app_key:
            app_key = self.init_config.get("app_key", "")
            
            # if no app key found throw an exception
            if not app_key:
                raise ConfigurationError("No app key found")
            
        options = {
            "Content-Type": "Application/json",
            "DD-API-KEY": api_key,
            "DD-APPLICATION-KEY": app_key
        }
        
        return options
    
    def validate_config(self):
        """
        This function validates that the required config is present in the conf.yaml
        """

        if self.dd_site not in API_URL_MAP.keys():
            raise ConfigurationError("Please provide a valid Datadog site - com, eu, us3, us5, or gov")
    
    def obf_text(self, secret_text):
        """
        function to obfuscate text and only display the last 4 characters, except in the case of strings
        that are 8 characters or less, then it obfuscates the entire string. this is used for logging
        which api key retrieving the related org name failed on, without having to write the entire api key
        to the log
        
        args:
            secret_text (str): text to obfuscate
            
        returns:
            (str): text with everything but the last 4 characters obfuscated, except where the string is
                   8 characters or less, then it will be a string of equivalent length only containing astericies
        """
        text_len = len(secret_text)
        
        if text_len <= 8: # probably shouldn't display 4 characters of an 8 char secret string
            return ''.join('*' * text_len)
        else:
            return ''.join('*' * (text_len - 4)) + secret_text[-4:]
    
    def get_org(self, options, retries=3):
        """
        recursive function to retrieve the org name related to the current api/app key being used.
        timeout for each request is hardcoded to 10 seconds. it only needs to retrieve the org name on
        initialization, and is necessary for tagging metrics by org, therefor if this fails all retries
        it throws an uncaught exception, halting the integration
        
        args:
            options (dict): dictionary containing the current instance's api and app key
            retries (int): default 3, number of times to retry getting the org name
            
        returns:
            org_name (str): name of the org associate with the current api/app key. in multi org accounts
                            it will choose the first account it finds marked 'parent_billing' in its billing type
        """
        
        try:
            response = self.http.get("https://{}/api/v1/org".format(self.api_url), extra_headers=self.options, timeout=10)
            response.raise_for_status()
            
            orgs = response.json().get("orgs", [])
            org_name = ""
            
            # use parent_billing for name from multi org accounts
            if len(orgs) > 1:
                for org in orgs:
                    if org.get("billing", {}).get("type", "") == "parent_billing":
                        org_name = org.get("name", "")
                        break
            else:
                org_name = orgs[0].get("name", "")
                
            return org_name
            
        except HTTPError as e:
            self.log.error("Failed retrieving org for api key: {}, retries left: {}".format(self.obf_text(options.get("api_key", "")), retries))
            if retries > 0:
                return self.get_org(options, retries-1)
            else:
                self.log.error("Failed final retry while retrieving org. traceback: {}".format(traceback.format_exc()))
                raise e
                
    def validate_agent(self, host):
        """
        This function checks if agents are installed on the hosts
                                      
        args:
            host (dict): host dictionary containing all relevant host data from the Datadog api
        """
        if not set(host.get("apps")).intersection(IGNORE_APPS):
            hostname = host.get("name", "")
            metric_tags = self.tags.copy()

            if hostname:
                metric_tags.append("validated_host:{}".format(hostname))
            
            metric_tags.append("org:{}".format(self.org))
            source_list = host.get("sources", [])

            host_meta = host.get("meta", {})

            # Checks if agent is present in the source list, and tags the metrics with the version
            if ("agent" in source_list) and host_meta and ("agent_version" in host_meta.keys()):
                string_version = host_meta.get("agent_version", "")
                agent_version = parse_version(host_meta.get("agent_version", ""))
                metric_tags.append("agent_version:{}".format(string_version))
                if string_version.startswith("6"):
                    if agent_version > parse_version("6.16.9") and agent_version < parse_version("6.32.2"):
                        self.gauge("agent.is_log4j_vulnerable", 1, tags=metric_tags, hostname=None)
                    else:
                        self.gauge("agent.is_log4j_vulnerable", 0, tags=metric_tags, hostname=None)
                elif string_version.startswith("7"):
                    if agent_version > parse_version("7.16.9") and agent_version < parse_version("7.32.2"):
                        self.gauge("agent.is_log4j_vulnerable", 1, tags=metric_tags, hostname=None)
                    else:
                        self.gauge("agent.is_log4j_vulnerable", 0, tags=metric_tags, hostname=None)
            
                self.gauge("agent.checked", 1, tags=metric_tags, hostname=None)
    
    def is_ignored_host(self, hostname):
        """
        function checks if the passed in hostname matches any of the regex for ignored hosts returning
        true if it is an ignored host, and false otherwise. case insensitive regex matching
        
        args:
            hostname (str): hostname to check against ignored host regexes
            
        returns:
            (bool): True if the host matches an ignored host regex (should be ignored), 
                    otherwise False (should be validated)
        """
        for ignored_host_regex in self.ignore_hosts:
            if re.match(ignored_host_regex, hostname, re.I):
                return True
                
        return False
