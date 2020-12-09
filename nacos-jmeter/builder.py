from pathlib import Path
import os
import re
import textwrap
import xml.etree.ElementTree as ET

from loguru import logger
import yaml

from rule import Rule
import settings


class Builder(object):
    """
    Class representing once Jenkins build with ant-jmeter.

    Note:
        1. The Nacos snapshot path was hardcoded to "../snapshot", make sure it exists.
        2. Test plan written in nacos.jmeter.test-plan must not start with "/".
    """
    def __init__(
            self,
            jenkins_job_name,
            jenkins_job_workspace,
            jmeter_home,
            test_name,
            test_plan_base_dir
    ):
        """
        Init a new Jenkins build.

        :param jenkins_job_name: name of Jenkins job, for example, debug-fullTest-Core400SUSR-Cloud-API-ci
        :param jenkins_job_workspace: workspace of job where test results were saved
        :param jmeter_home: JMeter home
        :param test_name: name for given test
        :param test_plan_base_dir: directory that stores all test plans, in particular, the local git repository
        """
        self.sample_build_xml = "../resources/build_template.xml"
        self.nacos_snapshot = "../snapshot"
        self.jenkins_job_name = jenkins_job_name
        self.jenkins_job_workspace = jenkins_job_workspace
        self.jmeter_home = jmeter_home
        self.test_name = test_name
        self.test_plan_base_dir = test_plan_base_dir

        self.stage = self._get_test_stage_from_job_name()
        self.debug = self._debug()
        self.job_name_without_modifier = self._remove_modifiers()
        self.test_plan = self._get_jmeter_test_plan()
        self.test_plan_abs_path = self._test_plan_abs()
        # additional properties, multi-properties should be separated by ','
        self.additional_properties = self.collect_property_files()

    def _get_test_stage_from_job_name(self):
        """Get test stage from the jenkins job name."""
        lowercase_job_name = self.jenkins_job_name.lower()
        if lowercase_job_name.endswith("ci"):
            stage = "ci"
        elif lowercase_job_name.endswith("testonline"):
            stage = "testonline"
        elif lowercase_job_name.endswith("predeploy"):
            stage = "predeploy"
        else:
            raise ValueError(
                f"Your job name {self.jenkins_job_name} are supposed to end with either one of "
                f"'ci', 'testonline' and 'predeploy' (case insensitive)"
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
        job_name_without_modifier = re.sub("(?i)[-|_](ci|testonline|predeploy)", "", job_name_without_modifier)
        logger.info(f"Job name without modifiers: {job_name_without_modifier}")
        return job_name_without_modifier

    def _get_jmeter_test_plan(self):
        """
        Get the JMeter test plan from nacos.jmeter.test-plan.
        Only relative path (relative to ) are accepted.
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
        test_plan = yaml_to_dict[self.job_name_without_modifier]
        assert not test_plan.startswith("/"), "only relative path was accepted"
        return test_plan

    def _test_plan_abs(self):
        """
        Get the absolute path of test plan.
        """
        test_plan_full_path = os.path.join(self.test_plan_base_dir, self.test_plan)
        assert os.path.exists(test_plan_full_path), f"file or directory {test_plan_full_path} does not exist"
        return test_plan_full_path

    def collect_property_files(self) -> list:
        """
        Collect property files (absolute path) for a Jenkins job.
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
        assert self.test_plan in yaml_to_dict.keys(), \
            f"The key named with JMeter test plan '{self.test_plan}' not defined in file {jenkins_and_jmeter_conf}"
        devices = yaml_to_dict[self.test_plan]

        # initiate a rule instance
        r = Rule(['cross-env', self.stage], devices, self.debug)

        # apply rule to snapshot
        config_path_list = r.apply_to_snapshot(self.nacos_snapshot)

        # join and generate path
        paths = []
        nacos_snapshot_abs = os.path.abspath(self.nacos_snapshot)
        for config_path in config_path_list:
            paths.append(os.path.join(nacos_snapshot_abs, *config_path))

        return paths

    def concatenate_property_files(self, out: str, to_stdout=False):
        """
        Combine content of several files, and save it to another file.
        :param out: file to save concatenated text
        :param to_stdout: print to stdout if set True
        """
        with open(out, "w") as out_file:
            # print("# all properties collected", file=out_file)
            out_file.write("# all properties collected from Nacos snapshot")
            for file in self.additional_properties:
                # out_file.write(f"# file: {file}\n")
                header = textwrap.dedent(f"""\n
                #=============== properties collected from ===============
                # {file}
                #=========================================================
                """)
                print(header, file=out_file)
                with open(file, 'r') as in_file:
                    # shutil.copyfileobj(in_file, out_file)
                    out_file.write(in_file.read())

        if to_stdout:
            with open(out, 'r') as out_file:
                print(out_file.read())

    def generate_new_build_xml(self, output_build_xml):
        """
        Generate a new build.xml.

        :param output_build_xml: new build.xml generated based on template
        """
        # check if files / directories exist.
        assert os.path.exists(self.sample_build_xml), "file or directory {} does not exist".format(self.sample_build_xml)
        assert os.path.exists(self.jenkins_job_workspace), "file or directory {} does not exist".format(self.jenkins_job_workspace)
        assert os.path.exists(self.jmeter_home), "file or directory {} does not exist".format(self.jmeter_home)

        tree = ET.parse(self.sample_build_xml)
        jenkins_job_workspace_element = tree.find("property[@name='jenkins.job.workspace']")
        jmeter_home_element = tree.find("property[@name='jmeter.home']")
        test_name_element = tree.find("property[@name='test']")
        jmeter_element = tree.find(".//jmeter")

        jenkins_job_workspace_element.set("value", self.jenkins_job_workspace)
        jmeter_home_element.set("value", self.jmeter_home)

        jmeter_element.set("testplan", self.test_plan_abs_path)
        test_name_element.set("value", self.test_name)

        for item in self.additional_properties:
            assert item.startswith("/"), f"{item} is supposed to be a absolute path (starts with '/')."
            assert os.path.exists(item.strip()), "file or directory {} does not exist.".format(item)
            ET.SubElement(jmeter_element, "jmeterarg", attrib={"value": "-q{}".format(item.strip())})

        tree.write(output_build_xml)


if __name__ == "__main__":
    b = Builder("debug-fullTest-Core400SUSR-Cloud-API-ci", "../snapshot", "d:\\Program Files (x86)\\jmeter4.0", "test_name_core400susr", "d:\\03 mp products\\01 cg Git代码\\cloud-api-test")
    b.generate_new_build_xml("../test/out.xml")
    b.concatenate_property_files("../test/all.properties")