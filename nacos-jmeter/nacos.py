from pathlib import Path
import os

from loguru import logger
import requests
import yaml

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


class Rule(object):
    """Class representing rules describing how to download configurations from Nacos for JMeter test plan."""

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

        :param namespaces: a list, whose element can only be one of "cross-env", "ci", "testonline", or "predeploy"
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

    def _collect_one_namespace(self, nacos: Nacos, namespace: str, **options) -> list:
        """
        Collect and return configurations existed from one Nacos namespace.

        1. Each element of the returned list is a tuple of (namespace, group, data_id).
        2. Parameter 'options' adds functionalities like downloading configurations.
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
        Collect and return configurations existed in Nacos based on the rule.

        1. Each element of the returned list is a tuple of (namespace, group, data_id).
        2. Parameter options adds functionalities like downloading configurations.

        :param nacos: instance of class Nacos
        :param options: additional functionalities like downloading configurations
        :return: list
        """
        data_id_paths = []
        for namespace in self.namespaces:
            logger.info(f"Begin to extract namespace: {namespace}")
            data_id_paths += self._collect_one_namespace(nacos, namespace, **options)
            logger.info(f"End to extract namespace: {namespace}")

        return data_id_paths

    def apply_to_snapshot(self, snapshot) -> list:
        """
        Collect and return configurations existed in local snapshot based on the rule.
        Each element of the returned list is an absolute path as "/path/to/snapshot/namespace/group/data_id"

        :param snapshot: directory contains snapshot of Nacos
        :return: list
        """
        data_id_tuples = []
        assert Path(snapshot).exists(), f"Error. Directory {snapshot} does not exist."
        for namespace in self.namespaces:
            logger.info(f"Begin to check namespace: {namespace}")
            for group in self.groups:
                group_name = group["group"]
                data_ids = group["data_ids"]
                for data_id in data_ids:
                    if Path(f"{snapshot}/{namespace}/{group_name}/{data_id}").exists():
                        logger.info(f"namespace: {namespace}, group: {group_name}, data id: {data_id} exists")
                        data_id_tuples.append((namespace, group_name, data_id))
            logger.info(f"End to check namespace: {namespace}")

        nacos_snapshot_abs = os.path.abspath(snapshot)
        data_id_abs_paths = []
        for config_path in data_id_tuples:
            data_id_abs_paths.append(os.path.join(nacos_snapshot_abs, *config_path))

        return data_id_abs_paths
