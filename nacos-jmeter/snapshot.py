from multiprocessing import Pool
from pathlib import Path
import json
import os

from loguru import logger
import nacos
import requests


class Nacos(object):

    def __init__(self, host, port):
        """Init class."""
        self.host = host
        self.host_port = f"http://{host}:{port}"
        self.login_path = f"/nacos/#/login"
        self.login_url = f"{self.host_port}{self.login_path}"
        self.get_namespaces_path = f"/nacos/v1/console/namespaces"
        self.get_namespaces_url = f"{self.host_port}{self.get_namespaces_path}"
        assert self.is_website_online(), f"Error. Cannot open login page {self.login_url} now."

    def is_website_online(self):
        """Returns true if login url can be opened successfully."""
        logger.info(f"nacos login url: {self.login_url}")
        return requests.get(self.login_url).status_code == 200

    def _get_one_namespace_configs(self, namespace_id, namespace_name, namespace_config_count, snapshot_base):
        nacos_client = nacos.NacosClient(self.host, namespace=namespace_id)
        nacos_client.set_options(snapshot_base=snapshot_base)
        logger.info(f"Get configs from namespace: {namespace_name}")
        nacos_client.get_configs(page_size=namespace_config_count)

    def make_snapshot(self, snapshot_base):
        """
        Download all configurations of every namespace to local.
        Files with the same name will be overwritten.

        :param snapshot_base: Dir to store snapshot config files.
        """
        # get all namespaces information
        response = requests.get(self.get_namespaces_url).text
        logger.info(f"Response of {self.get_namespaces_path}: {response}")
        namespaces = json.loads(response)["data"]
        p = Pool(len(namespaces))
        for item in namespaces:
            namespace_id = item["namespace"]
            namespace_id = None if not namespace_id else namespace_id
            namespace_name = item["namespaceShowName"]
            namespace_config_count = item["configCount"]
            p.apply_async(self._get_one_namespace_configs, args=(namespace_id, namespace_name, namespace_config_count, snapshot_base))
        p.close()
        p.join()


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
            assert namespace in ['cross-env', 'ci', 'testonline', 'predeploy', 'production'], \
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
                        with open(config_file, "w", encoding="utf-8") as f:
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
