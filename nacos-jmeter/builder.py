from pathlib import Path
import json
import os
import re
import xml.etree.ElementTree as ET

from loguru import logger
import yaml

import settings


class Builder(object):
    """
    Class representing once Jenkins build with ant-jmeter.

    Note:
        1. The Nacos snapshot path was hardcoded to "../snapshot", make sure it exists.
        2. Test plan written in nacos.jmeter.test-plan must not start with "/".
    """
    def __init__(self, jenkins_job_name, snapshot_base):
        """
        Init a new Jenkins build.

        :param jenkins_job_name: name of Jenkins job, for example, debug-fullTest-Core400SUSR-Cloud-API-ci
        :param snapshot_base: Directory where nacos-snapshot.git located.
        """
        self.parallel = False
        self.sample_build_xml = "../resources/build_template.xml"
        self.jenkins_job_name = jenkins_job_name

        self.stage = self._get_test_stage_from_job_name()
        self.debug = self._debug()
        self.job_name_without_modifier = self._remove_modifiers()
        self.relative_path_test_plans = self._get_jmeter_relative_path_test_plans()

        self.nacos_snapshot_base = snapshot_base
        self.summary_namespace_id = settings.SUMMARY_NAMESPACE_ID
        self.summary_group = settings.SUMMARY_GROUP

        self.jenkins_and_jmeter_conf = os.path.join(self.nacos_snapshot_base, "+".join(
            [
                settings.JENKINS_JMX_RELATIONSHIP_DATA_ID,
                settings.JENKINS_JMX_RELATIONSHIP_GROUP,
                settings.JENKINS_JMX_RELATIONSHIP_NAMESPACE_ID
            ]
        ))
        self.stage_to_namespace_ids = settings.STAGE_TO_NAMESPACE_IDS


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
                f"{self.stage_to_namespace_ids.keys()}"
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
        assert Path(self.jenkins_and_jmeter_conf).exists(), f"File {self.jenkins_and_jmeter_conf} does not exist"
        with open(self.jenkins_and_jmeter_conf, "r") as f:
            yaml_to_dict = yaml.safe_load(f)
        assert self.job_name_without_modifier in yaml_to_dict.keys(), \
            f"The key named with Jenkins job '{self.job_name_without_modifier}' " \
            f"not defined in file {self.jenkins_and_jmeter_conf}"
        object_to_job_name = yaml_to_dict[self.job_name_without_modifier]
        logger.info(f"object assigned to {self.job_name_without_modifier}: {object_to_job_name}")

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

            # set attributes for each <jmeter> element
            jmeter_element = ET.Element("jmeter", attrib={
                "jmeterhome": jmeter_home,
                "testplan": abs_path_test_plan,
                "resultlog": result_jtl
            })

            # add sub element <jmeterarg> to <jmeter>
            stage_summary_property_file_name = "+".join(
                [f"{self.stage}", self.summary_group, self.summary_namespace_id]
            )
            stage_summary_property_file = os.path.join(self.nacos_snapshot_base, stage_summary_property_file_name)
            ET.SubElement(jmeter_element, "jmeterarg", attrib={"value": "-q{}".format(stage_summary_property_file)})

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

        tree.write(output_build_xml, encoding="utf-8")
