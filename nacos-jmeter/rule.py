import requests

from pathlib import Path
from loguru import logger

from nacos import Nacos


class Rule(object):
    """Class representing rules for downloading configurations from Nacos."""

    def __init__(self, namespaces: list, devices: list, debug=False):
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

        :param namespaces: a list, whose element can nly be one of "cross-env", "ci", "testonline", or "predeploy"
        :param devices: a list of devices
        :param debug: set True if used for debugging
        """
        # check parameters
        for namespace in namespaces:
            assert namespace in ['cross-env', 'ci', 'testonline', 'predeploy'], \
                f"Unrecognized namespace {namespace} (supposed to be one of cross-env, ci, testonline or predeploy)"

        # set namespaces
        self.namespaces = namespaces
        logger.info(f"namespaces of current rule: {self.namespaces}")

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
                "data_ids": devices
            }
            self.groups.append(debug_group)
        logger.info(f"groups of current rule: {self.groups}")

    def _extract_one_namespace(self, nacos: Nacos, namespace: str, **options) -> list:
        """
        Extract and return configurations existed from one Nacos namespace.

        1. Each element of the returned list is a tuple of (namespace, group, data_id).
        2. Parameter options adds functionalities like downloading configurations.
           Hierarchy of downloaded files would be dst_dir/namespace/group/dataId.

        :param nacos: instance of class Nacos
        :param namespace: name of namespace
        :param options: denotes additional functionalities like download configuration files
        :return: list
        """
        data_id_paths = []
        namespace_id = nacos.namespaces[namespace]["id"]
        for group in self.groups:
            group_name = group["group"]
            data_ids = group["data_ids"]
            for data_id in data_ids:
                payload = {
                    "tenant": namespace_id,
                    "group": group_name,
                    "dataId": data_id
                }
                response = requests.get(nacos.get_config_url, params=payload)

                # if configuration exists, download it and save data id path to list
                if response.status_code == 200:
                    data_id_paths.append((namespace, group_name, data_id))

                    # if the *options* dict contains key 'dst_dir', the existed configurations would be downloaded.
                    if "dst_dir" in options.keys():
                        dst_dir = options["dst_dir"]
                        assert Path(dst_dir).exists(), f"Error. Directory {dst_dir} does not exist."
                        group_dir = f"{dst_dir}/{namespace}/{group_name}"
                        config_file = f"{group_dir}/{data_id}"
                        Path(group_dir).mkdir(parents=True, exist_ok=True)
                        logger.info(f"namespace: {namespace}, group: {group_name}, data id: {data_id} - path: {config_file}")
                        content = response.text
                        logger.info(f"namespace: {namespace}, group: {group_name}, data id: {data_id} - content:\n{content}")
                        with open(config_file, "w") as f:
                            f.write(content)

        return data_id_paths

    def apply_to_nacos(self, nacos: Nacos, **options) -> list:
        """
        Extract and return configurations existed in Nacos based on the rule.

        1. Each element of the returned list is a tuple of (namespace, group, data_id).
        2. Parameter options adds functionalities like downloading configurations.

        :param nacos: instance of class Nacos
        :param options: additional functionalities like downloading configurations
        :return: list
        """
        data_id_paths = []
        for namespace in self.namespaces:
            logger.info(f"Begin to extract namespace: {namespace}")
            data_id_paths += self._extract_one_namespace(nacos, namespace, **options)
            logger.info(f"End to extract namespace: {namespace}")

        return data_id_paths

    def apply_to_snapshot(self, snapshot) -> list:
        """
        Extract and return configurations existed in local snapshot based on the rule.
        Each element of the returned list is a tuple of (namespace_id, group, data_id).

        :param snapshot: directory contains snapshot of Nacos
        :return: list
        """
        data_id_path = []
        assert Path(snapshot).exists(), f"Error. Directory {snapshot} does not exist."
        for namespace in self.namespaces:
            logger.info(f"Begin to check namespace: {namespace}")
            for group in self.groups:
                group_name = group["group"]
                data_ids = group["data_ids"]
                for data_id in data_ids:
                    if Path(f"{snapshot}/{namespace}/{group_name}/{data_id}").exists():
                        logger.info(f"namespace: {namespace}, group: {group_name}, data id: {data_id} exists")
                        data_id_path.append((namespace, group_name, data_id))
            logger.info(f"End to check namespace: {namespace}")

        return data_id_path


if __name__ == "__main__":
    nacos = Nacos("localhost", 8848)
    rule = Rule(["cross-env", "ci"], ["core400s", "core300s"], True)
    paths = rule.apply_to_nacos(nacos, dst_dir="../test")
    # paths = rule.apply_to_snapshot("../test/")
    print(paths)
