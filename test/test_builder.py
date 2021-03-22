import os
import sys
sys.path.append("../nacos-jmeter")

from builder import Builder
from testplan import TestPlan
import settings

jenkins_job_name = "fullTest-Core400SUS-Cloud-API-CI"
jenkins_job_workspace = os.path.join(settings.PROJECT_ROOT, "data")
jmeter_home = "d:/Program Files (x86)/apache-jmeter-5.4"
test_name = "test_name_01"
test_plan_base_dir = "d:/03 mp products/01 cg Git代码/cloud-api-test"
new_build_xml = os.path.join(settings.PROJECT_ROOT, "data", "build.xml")

build = Builder(jenkins_job_name)
for test_plan in build.relative_path_test_plans:
    test_plan_abs_path = build.abs_path_test_plan(test_plan_base_dir, test_plan)
    test_plan_instance = TestPlan(test_plan_abs_path)

    # if build.debug:
    #     test_plan_instance.set_on_sample_error(settings.ON_SAMPLE_ERROR_ACTION)

    test_plan_instance.change_controller_type()
    test_plan_instance.save(test_plan_abs_path)

build.generate_new_build_xml(jenkins_job_workspace, jmeter_home, test_name, test_plan_base_dir, new_build_xml)
