from pathlib import Path

from loguru import logger
import requests
import yaml

from rule import Rule
import settings


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
        assert self.is_website_online(), f"Error. Cannot open login page {self.login_url} now."

    def is_website_online(self):
        """Returns true if login url can be opened successfully."""
        logger.info(f"nacos login url: {self.login_url}")
        return requests.get(self.login_url).status_code == 200

    def make_snapshot(self, dst_dir):
        """
        Make snapshot of Nacos based on the global rule.
        Configurations in namespace 'public' will be downloaded yet.

        :param dst_dir: directory to store snapshot
        """
        # get rule for snapshot
        payload = {
            "group": settings.SNAPSHOT_RULE_GROUP,
            "dataId": settings.SNAPSHOT_RULE_DATA_ID
        }
        rules_yaml = requests.get(self.get_config_url, params=payload).text
        logger.info(f"snapshot rule content: \n{rules_yaml}")
        rules_dict = yaml.safe_load(rules_yaml)

        # make snapshot
        rule = Rule(rules_dict["namespaces"], rules_dict["devices"], True)
        rule.apply_to_nacos(self, dst_dir=dst_dir)

        # download configurations in namespace 'public'
        payload_jenkins_jmx_conf = {
            "group": settings.JENKINS_JMX_RELATIONSHIP_GROUP,
            "dataId": settings.JENKINS_JMX_RELATIONSHIP_DATA_ID
        }
        response = requests.get(self.get_config_url, params=payload_jenkins_jmx_conf)
        if response.status_code == 200:
            jenkins_jmx_conf_yaml = response.text
            jenkins_jmx_relationship_group_dir = f"{dst_dir}/public/{settings.JENKINS_JMX_RELATIONSHIP_GROUP}"
            Path(jenkins_jmx_relationship_group_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"jenkins jmx conf content: \n{jenkins_jmx_conf_yaml}")
            with open(f"{jenkins_jmx_relationship_group_dir}/{settings.JENKINS_JMX_RELATIONSHIP_DATA_ID}", "w") as f:
                f.write(jenkins_jmx_conf_yaml)


if __name__ == "__main__":
    n = Nacos("34.234.176.173", 8848)
    n.make_snapshot("../test")
