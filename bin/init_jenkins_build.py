from os import path
import sys
project_root = path.dirname(path.dirname(path.abspath(__file__)))
sys.path.append(f"{project_root}/nacos-jmeter")

from loguru import logger

from builder import Builder
from testplan import TestPlan

jenkins_job_name = sys.argv[1]
jenkins_job_workspace = sys.argv[2]
jmeter_home = sys.argv[3]
test_name = sys.argv[4]
test_plan_base_dir = sys.argv[5]
new_build_xml = sys.argv[6]
nacos_snapshot_base = sys.argv[7]
is_smoke_test = sys.argv[8]

build = Builder(jenkins_job_name, nacos_snapshot_base)
for test_plan in build.relative_path_test_plans:
    test_plan_abs_path = build.abs_path_test_plan(test_plan_base_dir, test_plan)
    test_plan_instance = TestPlan(test_plan_abs_path)

    # if build.debug:
    #     test_plan_instance.set_on_sample_error(settings.ON_SAMPLE_ERROR_ACTION)

    test_plan_instance.change_controller_type()

    if is_smoke_test == "true":
        logger.info("smoke test flag was set, add JSR223Listener to HTTP Request now.")
        test_plan_instance.add_jsr223listener_to_each_http_request(jenkins_job_name)

    test_plan_instance.save(test_plan_abs_path)

build.generate_new_build_xml(jenkins_job_workspace, jmeter_home, test_name, test_plan_base_dir, new_build_xml)
