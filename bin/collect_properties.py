from pathlib import Path
import os
import re
import sys
sys.path.append("../nacos-jmeter")

from loguru import logger
import yaml

import rule
import settings


def collect_properties(jenkins_job_name: str, nacos_snapshot: str) -> list:
    """
    Collect property files for a Jenkins job.

    :param jenkins_job_name: name of Jenkins job
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
            f"The job name {jenkins_job_name} must end with either one of 'ci', 'testonline' and 'predeploy'"
        )
    logger.info(f"Stage gotten from job name: {stage}")

    # determine if used for debugging
    if jenkins_job_name.startswith("debug"):
        debug = True

    # strip job name's prefix and suffix
    job_name_without_modifier = re.sub("(?i)(regression|debug)[-|_]", "", jenkins_job_name)
    job_name_without_modifier = re.sub("(?i)[-|_](ci|testonline|predeploy)]", "", job_name_without_modifier)
    logger.info(f"Job name without modifier: {job_name_without_modifier}")

    # get devices used in jmx
    nacos_jmeter_test_plan_conf = os.path.join(
        nacos_snapshot,
        "public",
        settings.JENKINS_JMX_RELATIONSHIP_GROUP,
        settings.JENKINS_JMX_RELATIONSHIP_DATA_ID
    )
    assert Path(nacos_jmeter_test_plan_conf).exists(), f"File {nacos_jmeter_test_plan_conf} does not exist"
    devices = yaml.safe_load(nacos_jmeter_test_plan_conf)