import json
import time

import requests
from loguru import logger


class NacosServer(object):
    """Class representing one Nacos server."""

    def __init__(self, host, port, wait_until_online=True):
        """Init class."""
        self.host = host
        self.host_port = f"http://{host}:{port}"
        self.login_path = f"/nacos/#/login"
        self.login_url = f"{self.host_port}{self.login_path}"
        self.get_namespaces_path = f"/nacos/v1/console/namespaces"
        self.get_namespaces_url = f"{self.host_port}{self.get_namespaces_path}"
        if wait_until_online:
            self.wait_until_online()

    def is_nacos_online(self):
        """Returns true if login url can be opened successfully."""
        logger.info(f"nacos login url: {self.login_url}")
        try:
            response = requests.get(self.login_url)
        except requests.exceptions.ConnectionError:
            logger.warning(f"Cannot connect to Nacos now.")
            return False

        if response.status_code == 200:
            logger.success("Nacos service is available now.")
            return True
        else:
            logger.warning("Nacos service is available, but cannot open login page now.")
            return False

    def wait_until_online(self):
        """Stop polling until Nacos server is available."""
        while not self.is_nacos_online():
            logger.info("Nacos server is not available now, try 10 seconds later again.")
            time.sleep(10)

    def get_namespaces(self):
        """Get all namespaces information."""
        response = requests.get(self.get_namespaces_url).text
        logger.info(f"Response of {self.get_namespaces_path}: {response}")
        return json.loads(response)["data"]

    def _namespace_name_to_id(self):
        """Build the relationship between namespace name and corresponding id."""
        namespaces = self.get_namespaces()
        return {n["namespaceShowName"]: n["namespace"] for n in namespaces}

    def _namespace_id_to_name(self):
        """Build the relationship between namespace id and corresponding name."""
        namespaces = self.get_namespaces()
        return {n["namespace"]: n["namespaceShowName"] for n in namespaces}
