import sys
sys.path.append("../nacos-jmeter")

from builder import Builder
from testplan import TestPlan
import settings

jenkins_job_name = sys.argv[1]
jenkins_job_workspace = sys.argv[2]
jmeter_home = sys.argv[3]
test_name = sys.argv[4]
test_plan_base_dir = sys.argv[5]
new_build_xml = sys.argv[6]

build = Builder(jenkins_job_name)
for test_plan in build.relative_path_test_plans:
    test_plan_abs_path = build.abs_path_test_plan(test_plan_base_dir, test_plan)
    test_plan_instance = TestPlan(test_plan_abs_path)

    # if build.debug:
    #     test_plan_instance.set_on_sample_error(settings.ON_SAMPLE_ERROR_ACTION)

    test_plan_instance.change_controller_type()
    test_plan_instance.save(test_plan_abs_path)

build.generate_new_build_xml(jenkins_job_workspace, jmeter_home, test_name, test_plan_base_dir, new_build_xml)
