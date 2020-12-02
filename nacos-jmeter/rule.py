import requests

from pathlib import Path
from loguru import logger

from nacos import Nacos


class Rule(object):
    """Class representing rules for downloading configurations from Nacos."""

    def __init__(self, env, devices: list, debug=False):
        """
        Init a rule for a JMeter test plan.

        IMPORTANT NOTES:
            1. Value of properties "namespaces" and "groups" are both Python lists to keep the order of elements
            2. The order of elements is important for configuration priority

        An example of rule instance:
            "namespaces": ["cross-env", "ci"],
            "groups": [{
                "group": "SHARED",
                "data_ids": ["common"]
            }, {
                "group": "DEVICE",
                "data_ids": ["core400s", "core300s"]
            }, {
                "group": "DEBUG",
                "data_ides": ["core400s", "core300s"]
            }]

        :param env: can nly be one of "ci", "testonline", or "predeploy"
        :param devices: a list of devices
        :param debug: set True if used for debugging
        """
        # check parameters
        assert env in ['ci', 'testonline', 'predeploy'], 'parameter "env" must be ci, testonline or predeploy'

        # set namespaces
        self.namespaces = ["cross-env", env]

        # set groups
        self.groups = [
            {
                "group": "SHARED",
                "data_ids": ["common"]
            },
            {
                "group": "DEVICE",
                "data_ids": devices
            }
        ]

        # add group DEBUG if parameter debug was set true
        if debug:
            debug_group = {
                "group": "DEBUG",
                "data_ides": devices
            }
            self.groups.append(debug_group)

    def _sync_one_namespace(self, nacos: Nacos, namespace: str, dst_dir: str) -> list:
        """
        Download configurations of specific namespace.

        Hierarchy of downloaded files would be as dst_dir/group/dataId.
        The destination directory name should be set to namespace name.

        :param nacos: instance of class Nacos
        :param namespace: name of namespace
        :param dst_dir: Directory to save configuration files
        :return: a list of (namespace_id, group, data_id) existed in Nacos
        """
        data_id_paths = []
        namespace_id = nacos.namespaces[namespace]["id"]
        for group in self.groups:
            group_name = group["group"]
            data_ids = group["data-ids"]
            group_dir = f"{dst_dir}/{group_name}"
            logger.info(f"group: {namespace}:{group_name} (data-ids: {data_ids}, path: {group_dir})")
            Path(group_dir).mkdir(parents=False, exist_ok=True)
            for data_id in data_ids:
                config_file = f"{group_dir}/{data_id}"
                logger.info(f"{namespace}:{group_name}:{data_id} file path: {config_file}")
                payload = {
                    "tenant": namespace_id,
                    "group": group_name,
                    "dataId": data_id
                }
                response = requests.get(nacos.get_config_url, params=payload)

                # if configuration exists, download it and save path to list
                if response.status_code == 200:
                    content = response.text
                    logger.info(f"{namespace}:{group_name}:{data_id}'s content : {content}")
                    with open(config_file, "w") as f:
                        f.write(content)
                    data_id_paths.append(tuple(payload.values()))

            return data_id_paths

    def apply_to_nacos(self, nacos: Nacos, dst_dir) -> list:
        """
        Download configuration files from Nacos based on rule.

        :param nacos: instance of class Nacos
        :param dst_dir: directory to store downloaded configuration files
        :return: a list of (namespace_id, group, data_id) existed in Nacos
        """
        data_id_paths = []
        for namespace in self.namespaces:
            namespace_dir = f"{dst_dir}/{namespace}"
            logger.info(f"Begin to sync namespace: {namespace} (path: {namespace_dir})")
            Path(namespace_dir).mkdir(parents=False, exist_ok=True)
            data_id_paths += self._sync_one_namespace(nacos, namespace, namespace_dir)
            logger.info(f"End to sync namespace: {namespace}")

        return data_id_paths










if __name__ == "__main__":
    rule = Rule("ci", ["core400s", "core300s"], True)
