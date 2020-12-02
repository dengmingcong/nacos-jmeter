from loguru import logger
import requests


class Nacos(object):

    def __init__(self, host, port):
        """Init class."""
        self.login_url = f"http://{host}:{port}/nacos/#/login"
        self.get_config_url = f"http://{host}:{port}/nacos/v1/cs/configs"
        self.namespaces = {
            "cross-env": {"id": "cross-env"},
            "ci": {"id": "env-01"},
            "testonline": {"id": "env-02"},
            "predeploy": {"id": "env-03"}
        }

    def is_website_online(self):
        """Returns true if login url can be opened successfully."""
        logger.info(f"nacos login url: {self.login_url}")
        return requests.get(self.login_url).status_code == 200
