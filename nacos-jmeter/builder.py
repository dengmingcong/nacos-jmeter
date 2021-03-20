from pathlib import Path
import json
import os
import re
import xml.etree.ElementTree as ET

from loguru import logger
import yaml

import common
import settings


class Builder(object):
    """
    Class representing once Jenkins build with ant-jmeter.

    Note:
        1. The Nacos snapshot path was hardcoded to "../snapshot", make sure it exists.
        2. Test plan written in nacos.jmeter.test-plan must not start with "/".
    """
    def __init__(self, jenkins_job_name):
        """
        Init a new Jenkins build.

        :param jenkins_job_name: name of Jenkins job, for example, debug-fullTest-Core400SUSR-Cloud-API-ci
        """
        self.parallel = False
        self.sample_build_xml = "../resources/build_template.xml"
        self.nacos_snapshot = "../snapshot"
        self.jenkins_job_name = jenkins_job_name

        self.stage = self._get_test_stage_from_job_name()
        self.debug = self._debug()
        self.job_name_without_modifier = self._remove_modifiers()
        self.relative_path_test_plans = self._get_jmeter_relative_path_test_plans()

    def _get_test_stage_from_job_name(self):
        """Get test stage from the jenkins job name."""
        lowercase_job_name = self.jenkins_job_name.lower()
        if lowercase_job_name.endswith("ci"):
            stage = "ci"
        elif lowercase_job_name.endswith("testonline"):
            stage = "testonline"
        elif lowercase_job_name.endswith("predeploy"):
            stage = "predeploy"
        elif lowercase_job_name.endswith("production"):
            stage = "production"
        else:
            raise ValueError(
                f"Your job name {self.jenkins_job_name} are supposed to end with either one of "
                f"'ci', 'testonline', 'predeploy' or 'production' (case insensitive)"
            )
        logger.info(f"Stage gotten from job name: {stage}")
        return stage

    def _debug(self):
        """Return true if the job name starts with debug (case insensitive)."""
        lowercase_job_name = self.jenkins_job_name.lower()
        return lowercase_job_name.startswith("debug")

    def _remove_modifiers(self):
        """Remove prefix and suffix of job name."""
        job_name_without_modifier = re.sub("(?i)(regression|debug)[-|_]", "", self.jenkins_job_name)
        job_name_without_modifier = re.sub("(?i)[-|_](ci|testonline|predeploy|production)", "", job_name_without_modifier)
        logger.info(f"Job name without modifiers: {job_name_without_modifier}")
        return job_name_without_modifier

    def set_parallel(self, data: dict) -> list:
        """
        Set parallel based on key 'parallel'.
        :param data: a dict, which contains required key "testplans" and optional "parallel"
        """
        assert "testplans" in data.keys(), f"Key 'testplans' must exist in the dict {data}."
        test_plans = data["testplans"]
        assert isinstance(test_plans, list) or isinstance(test_plans, str), \
            f"Values assigned to 'testplans' must be an instance of list or str."
        if "parallel" in data.keys():
            assert isinstance(data["parallel"], bool), "Value assigned to 'parallel' must be boolean."
            self.parallel = data["parallel"]
        logger.info(f"self.parallel is set to: {self.parallel}")
        return test_plans

    def _get_jmeter_relative_path_test_plans(self) -> list:
        """
        Get the JMeter test plans from nacos.jmeter.test-plan.
        Only relative path (relative to repository root) are accepted.
        :return: a list of test plans
        """
        jenkins_and_jmeter_conf = os.path.join(
            self.nacos_snapshot,
            "public",
            settings.JENKINS_JMX_RELATIONSHIP_GROUP,
            settings.JENKINS_JMX_RELATIONSHIP_DATA_ID
        )
        assert Path(jenkins_and_jmeter_conf).exists(), f"File {jenkins_and_jmeter_conf} does not exist"
        with open(jenkins_and_jmeter_conf, "r") as f:
            yaml_to_dict = yaml.safe_load(f)
        assert self.job_name_without_modifier in yaml_to_dict.keys(), \
            f"The key named with Jenkins job '{self.job_name_without_modifier}' not defined in file {jenkins_and_jmeter_conf}"
        object_to_job_name = yaml_to_dict[self.job_name_without_modifier]
        logger.info(f"object assigned to {self.job_name_without_modifier}: {object_to_job_name}")

        test_plans = []
        if isinstance(object_to_job_name, str):
            test_plans = [object_to_job_name]
        elif isinstance(object_to_job_name, list):
            test_plans = object_to_job_name
        elif isinstance(object_to_job_name, dict):
            if self.stage in object_to_job_name.keys():
                object_to_stage = object_to_job_name[self.stage]
                logger.info(f"object assigned to {self.stage}: {object_to_stage}")
                if isinstance(object_to_stage, str):
                    test_plans = [object_to_stage]
                elif isinstance(object_to_stage, list):
                    test_plans = object_to_stage
                elif isinstance(object_to_stage, dict):
                    test_plans = self.set_parallel(object_to_stage)
                else:
                    raise ValueError(f"Object assigned to {self.stage} can only be string, list or dict.")
            else:
                test_plans = self.set_parallel(object_to_job_name)
        else:
            raise ValueError(f"Object assigned to {self.job_name_without_modifier} can only be string, list or dict.")

        for test_plan in test_plans:
            assert not test_plan.startswith("/"), f"only relative path was accepted, but {test_plan} starts with '/'"

        logger.debug(f"all test plans got: {test_plans}")
        return test_plans

    @staticmethod
    def abs_path_test_plan(base_dir, relative_path_test_plan):
        """
        Get the absolute path of test plans.

        :param base_dir: directory that stores all test plans, in particular, the local git repository
        :param relative_path_test_plan: test plan relative to base directory
        """
        abs_path_test_plan = os.path.join(base_dir, relative_path_test_plan)
        assert os.path.exists(abs_path_test_plan), f"file or directory {abs_path_test_plan} does not exist"
        return abs_path_test_plan

    def collect_property_files(self, relative_path_test_plan) -> list:
        """
        Collect property files (absolute path) for a JMeter test plan.
        :param relative_path_test_plan: test plan relative to base directory
        :return: list of property files
        """
        jenkins_and_jmeter_conf = os.path.join(
            self.nacos_snapshot,
            "public",
            settings.JENKINS_JMX_RELATIONSHIP_GROUP,
            settings.JENKINS_JMX_RELATIONSHIP_DATA_ID
        )
        assert Path(jenkins_and_jmeter_conf).exists(), f"File {jenkins_and_jmeter_conf} does not exist"
        with open(jenkins_and_jmeter_conf, "r") as f:
            yaml_to_dict = yaml.safe_load(f)
        assert relative_path_test_plan in yaml_to_dict.keys(), \
            f"The key named with JMeter test plan '{relative_path_test_plan}' not defined in file {jenkins_and_jmeter_conf}"

        devices = yaml_to_dict[relative_path_test_plan]
        assert isinstance(devices, str) or isinstance(devices, list), "devices can only be string or list."

        if isinstance(devices, str):
            devices = [devices]

        # initiate a rule instance
        r = Rule(['cross-env', self.stage], devices, self.debug)

        # apply rule to snapshot
        paths = r.apply_to_snapshot(self.nacos_snapshot)

        return paths

    def generate_new_build_xml(
            self,
            jenkins_job_workspace,
            jmeter_home,
            test_name,
            test_plan_base_dir,
            output_build_xml):
        """
        Generate a new build.xml.

        :param jenkins_job_workspace: workspace of job where test results were saved
        :param jmeter_home: JMeter home
        :param test_name: name for given test
        :param test_plan_base_dir: directory that stores all test plans, in particular, the local git repository
        :param output_build_xml: new build.xml generated based on template
        """
        # check if files / directories exist.
        assert os.path.exists(self.sample_build_xml), "file or directory {} does not exist".format(self.sample_build_xml)
        assert os.path.exists(jenkins_job_workspace), "file or directory {} does not exist".format(jenkins_job_workspace)
        assert os.path.exists(jmeter_home), "file or directory {} does not exist".format(jmeter_home)

        # find elements to be reassigned
        tree = ET.parse(self.sample_build_xml)
        jenkins_job_workspace_element = tree.find("property[@name='jenkins.job.workspace']")
        jmeter_home_element = tree.find("property[@name='jmeter.home']")
        test_name_element = tree.find("property[@name='test']")
        target_run_element = tree.find("target[@name='run']")
        target_xslt_report_element = tree.find("target[@name='xslt-report']")

        # set jenkins workspace, jmeter home, and test name
        jenkins_job_workspace_element.set("value", jenkins_job_workspace)
        jmeter_home_element.set("value", jmeter_home)
        test_name_element.set("value", test_name)

        # create element "parallel"
        ant_parallel_element = ET.Element("parallel")
        if self.parallel:
            target_run_element.append(ant_parallel_element)

        # list every test plan under target "run", showed as <jmeter> element
        jmx_file_names = []
        for test_plan in self.relative_path_test_plans:
            jmx_file_name = os.path.splitext(os.path.basename(test_plan))[0]
            jmx_file_names.append(jmx_file_name)
            result_jtl = f"{jenkins_job_workspace}/{jmx_file_name}.jtl"
            result_html = f"{jenkins_job_workspace}/reports/{jmx_file_name}.html"
            abs_path_test_plan = self.abs_path_test_plan(test_plan_base_dir, test_plan)

            # collect properties
            print("Collect properties for test plan: " + test_plan)
            additional_properties = self.collect_property_files(test_plan)

            # name property file with extension ".utf8" for later conversion in ant task native2ascii
            src_concatenated_property_file = f"{jenkins_job_workspace}/{jmx_file_name}.utf8"
            dst_concatenated_property_file = f"{jenkins_job_workspace}/{jmx_file_name}.properties"
            common.concatenate_files(additional_properties, src_concatenated_property_file, True)

            # set attributes for each <jmeter> element
            jmeter_element = ET.Element("jmeter", attrib={
                "jmeterhome": jmeter_home,
                "testplan": abs_path_test_plan,
                "resultlog": result_jtl
            })

            # add sub element <jmeterarg> to <jmeter>
            ET.SubElement(jmeter_element, "jmeterarg", attrib={"value": "-q{}".format(dst_concatenated_property_file)})

            if self.parallel:
                ant_parallel_element.append(jmeter_element)
            else:
                target_run_element.append(jmeter_element)

            # add xslt element for each test plan
            xslt_element = ET.Element("xslt", {
                "classpathref": "xslt.classpath",
                "force": "true",
                "in": result_jtl,
                "out": result_html,
                "style": f"{jmeter_home}/extras/jmeter.results.foldable.xsl"
            })
            target_xslt_report_element.append(xslt_element)

        # save file names of all test plans to file jmx.json, used to prepend [PASS] or [FAIL] based on jtl
        with open(f"{jenkins_job_workspace}/jmx.json", "w") as f:
            json.dump(jmx_file_names, f)

        tree.write(output_build_xml)


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

    def _collect_one_namespace(self, nacos: NacosSyncer, namespace: str, **options) -> list:
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

    def apply_to_nacos(self, nacos: NacosSyncer, **options) -> list:
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
