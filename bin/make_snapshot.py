import sys
sys.path.append("../nacos-jmeter")

from pathlib import Path

from loguru import logger
import requests
import yaml

import settings
from nacos import Nacos
from rule import Rule


def make_snapshot(nacos: Nacos, dst_dir):
    """
    Make snapshot of Nacos based on the global rule.

    Configurations in namespace 'public' will be downloaded yet.
    """
    assert nacos.is_website_online(), f"Error. Cannot open login page {nacos.login_url} now."

    # get rule for snapshot
    payload = {
        "group": settings.SNAPSHOT_RULE_GROUP,
        "dataId": settings.SNAPSHOT_RULE_DATA_ID
    }
    rules_yaml = requests.get(nacos.get_config_url, params=payload).text
    logger.info(f"snapshot rule content: \n{rules_yaml}")
    rules_dict = yaml.safe_load(rules_yaml)

    # make snapshot
    rule = Rule(rules_dict["namespaces"], rules_dict["devices"], True)
    rule.apply_to_nacos(nacos, dst_dir=dst_dir)

    # download configurations in namespace 'public'
    payload_jenkins_jmx_conf = {
        "group": settings.JENKINS_JMX_RELATIONSHIP_GROUP,
        "dataId": settings.JENKINS_JMX_RELATIONSHIP_DATA_ID
    }
    response = requests.get(nacos.get_config_url, params=payload_jenkins_jmx_conf)
    if response.status_code == 200:
        jenkins_jmx_conf_yaml = response.text
        jenkins_jmx_relationship_group_dir = f"{dst_dir}/public/{settings.JENKINS_JMX_RELATIONSHIP_GROUP}"
        Path(jenkins_jmx_relationship_group_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"jenkins jmx conf content: \n{jenkins_jmx_conf_yaml}")
        with open(f"{jenkins_jmx_relationship_group_dir}/{settings.JENKINS_JMX_RELATIONSHIP_DATA_ID}", "w") as f:
            f.write(jenkins_jmx_conf_yaml)


if __name__ == "__main__":
    snapshot_dir = sys.argv[1]
    nacos_new = Nacos(settings.HOST, settings.PORT)
    make_snapshot(nacos_new, snapshot_dir)
