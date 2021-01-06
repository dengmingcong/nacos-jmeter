from pathlib import Path
import json
import os
import re
import xml.etree.ElementTree as ET

from loguru import logger
import yaml

import common
from snapshot import Rule
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

    def _get_jmeter_relative_path_test_plans(self) -> list:
        """
        Get the JMeter test plans from nacos.jmeter.test-plan.
        Only relative path (relative to ) are accepted.
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
        test_plans = yaml_to_dict[self.job_name_without_modifier]
        assert isinstance(test_plans, str) or isinstance(test_plans, list) or isinstance(test_plans, dict), \
            "test plan can only be string, list or dict."

        # TODO: simplify code
        if isinstance(test_plans, str):
            test_plans = [test_plans]
        elif isinstance(test_plans, dict):
            test_plans = test_plans[self.stage]
            if isinstance(test_plans, str):
                test_plans = [test_plans]

        for test_plan in test_plans:
            assert not test_plan.startswith("/"), f"only relative path was accepted, but {test_plan} starts with '/'"

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

        tree = ET.parse(self.sample_build_xml)
        jenkins_job_workspace_element = tree.find("property[@name='jenkins.job.workspace']")
        jmeter_home_element = tree.find("property[@name='jmeter.home']")
        test_name_element = tree.find("property[@name='test']")
        target_run_element = tree.find("target[@name='run']")
        target_xslt_report_element = tree.find("target[@name='xslt-report']")

        jenkins_job_workspace_element.set("value", jenkins_job_workspace)
        jmeter_home_element.set("value", jmeter_home)
        test_name_element.set("value", test_name)

        jmx_file_names = []
        for test_plan in self.relative_path_test_plans:
            jmx_file_name = os.path.splitext(os.path.basename(test_plan))[0]
            jmx_file_names.append(jmx_file_name)
            result_jtl = f"{jenkins_job_workspace}/{jmx_file_name}.jtl"
            result_html = f"{jenkins_job_workspace}/reports/{jmx_file_name}.html"
            abs_path_test_plan = self.abs_path_test_plan(test_plan_base_dir, test_plan)

            print("Collect properties for test plan: " + test_plan)
            # additional properties, multi-properties should be separated by ','
            additional_properties = self.collect_property_files(test_plan)
            concatenated_property_file = f"{jenkins_job_workspace}/{jmx_file_name}.properties"
            common.concatenate_files(additional_properties, concatenated_property_file, True)

            # call native2ascii to convert property file to fit ISO 8859-1
            # common.convert_property_file(concatenated_property_file, concatenated_property_file)

            ET.SubElement(target_run_element, "delete", attrib={"file": result_jtl})
            jmeter_element = ET.Element("jmeter", attrib={
                "jmeterhome": jmeter_home,
                "testplan": abs_path_test_plan,
                "resultlog": result_jtl
            })

            ET.SubElement(jmeter_element, "jmeterarg", attrib={"value": "-q{}".format(concatenated_property_file)})
            target_run_element.append(jmeter_element)

            xslt_element = ET.Element("xslt", {
                "classpathref": "xslt.classpath",
                "force": "true",
                "in": result_jtl,
                "out": result_html,
                "style": f"{jmeter_home}/extras/jmeter.results.foldable.xsl"
            })
            target_xslt_report_element.append(xslt_element)

        with open(f"{jenkins_job_workspace}/jmx.json", "w") as f:
            json.dump(jmx_file_names, f)
        tree.write(output_build_xml)
