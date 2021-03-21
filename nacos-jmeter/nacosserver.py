import json

import requests
from loguru import logger


class NacosServer(object):
    """Class representing one Nacos server."""

    def __init__(self, host, port):
        """Init class."""
        self.host = host
        self.host_port = f"http://{host}:{port}"
        self.login_path = f"/nacos/#/login"
        self.login_url = f"{self.host_port}{self.login_path}"
        self.get_namespaces_path = f"/nacos/v1/console/namespaces"
        self.get_namespaces_url = f"{self.host_port}{self.get_namespaces_path}"
        assert self._is_nacos_online(), f"Error. Cannot open login page {self.login_url} now."
        self.namespaces = self._set_namespaces()

    def _is_nacos_online(self):
        """Returns true if login url can be opened successfully."""
        logger.info(f"nacos login url: {self.login_url}")
        return requests.get(self.login_url).status_code == 200

    def _set_namespaces(self):
        """Get all namespaces information."""
        response = requests.get(self.get_namespaces_url).text
        logger.info(f"Response of {self.get_namespaces_path}: {response}")
        return json.loads(response)["data"]
