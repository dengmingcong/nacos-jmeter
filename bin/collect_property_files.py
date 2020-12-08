from pathlib import Path
import os
import re
import sys
sys.path.append("../nacos-jmeter")

from loguru import logger
import yaml

from rule import Rule
import settings


def collect_property_files(jenkins_job_name: str, nacos_snapshot: str) -> list:
    """
    Collect property files for a Jenkins job.

    :param jenkins_job_name: name of Jenkins job, for example, debug-fullTest-Core400SUSR-Cloud-API-ci
    :param nacos_snapshot: directory contains snapshot of Nacos
    :return: list of property files
    """
    # determine test stage
    lowercase_job_name = jenkins_job_name.lower()
    stage = ""
    if lowercase_job_name.endswith("ci"):
        stage = "ci"
    elif lowercase_job_name.endswith("testonline"):
        stage = "testonline"
    elif lowercase_job_name.endswith("predeploy"):
        stage = "predeploy"
    else:
        raise ValueError(
            f"Your job name {jenkins_job_name} are supposed to end with either one of "
            f"'ci', 'testonline' and 'predeploy' (case insensitive)"
        )
    logger.info(f"Stage gotten from job name: {stage}")

    # determine if used for debugging
    debug = False
    if jenkins_job_name.startswith("debug"):
        debug = True

    # strip job name's prefix and suffix
    job_name_without_modifier = re.sub("(?i)(regression|debug)[-|_]", "", jenkins_job_name)
    job_name_without_modifier = re.sub("(?i)[-|_](ci|testonline|predeploy)", "", job_name_without_modifier)
    logger.info(f"Job name without modifiers: {job_name_without_modifier}")

    # get devices used in jmx
    jenkins_and_jmeter_conf = os.path.join(
        nacos_snapshot,
        "public",
        settings.JENKINS_JMX_RELATIONSHIP_GROUP,
        settings.JENKINS_JMX_RELATIONSHIP_DATA_ID
    )
    assert Path(jenkins_and_jmeter_conf).exists(), f"File {jenkins_and_jmeter_conf} does not exist"
    with open(jenkins_and_jmeter_conf, "r") as f:
        yaml_to_dict = yaml.safe_load(f)
    assert job_name_without_modifier in yaml_to_dict.keys(), \
        f"The key named with Jenkins job '{job_name_without_modifier}' not defined in file {jenkins_and_jmeter_conf}"
    test_plan = yaml_to_dict[job_name_without_modifier]
    assert test_plan in yaml_to_dict.keys(), \
        f"The key named with JMeter test plan '{test_plan}' not defined in file {jenkins_and_jmeter_conf}"
    devices = yaml_to_dict[test_plan]

    # initiate a rule instance
    r = Rule(['cross-env', stage], devices, debug)

    # apply rule to snapshot
    config_path_list = r.apply_to_snapshot(nacos_snapshot)

    # join and generate path
    paths = []
    for config_path in config_path_list:
        paths.append(os.path.join(nacos_snapshot, *config_path))

    return paths


if __name__ == "__main__":
    print(collect_property_files("debug-fullTest-Core400SUSR-Cloud-API-ci", "../test"))
