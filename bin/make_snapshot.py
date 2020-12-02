from loguru import logger
import requests
import yaml

import settings
from nacos import Nacos
from rule import Rule


def make_snapshot(nacos: Nacos, dst_dir):
    """
    Make snapshot of Nacos based on specific rules.
    """
    assert nacos.is_website_online(), f"Error. Cannot open login page {nacos.login_url} now."

    # get rule for snapshot
    payload = {
        "group": settings.SNAPSHOT_RULE_GROUP,
        "dataId": settings.SNAPSHOT_RULE_DATA_ID
    }
    rules_yaml = requests.get(nacos.get_config_url, params=payload).text
    logger.info(f"YAML content: \n{rules_yaml}")
    rules_dict = yaml.safe_load(rules_yaml)

    # make snapshot
    rule = Rule(rules_dict["namespaces"], rules_dict["devices"], True)
    rule.apply_to_nacos(nacos, dst_dir=dst_dir)


if __name__ == "__main__":
    nacos_new = Nacos(settings.HOST, settings.PORT)
    make_snapshot(nacos_new, "../test")
