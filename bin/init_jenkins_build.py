import sys
sys.path.append("../nacos-jmeter")

from builder import Builder
from testplan import TestPlan
import common

jenkins_job_name = sys.argv[1]
jenkins_job_workspace = sys.argv[2]
jmeter_home = sys.argv[3]
test_name = sys.argv[4]
test_plan_base_dir = sys.argv[5]
new_build_xml = sys.argv[6]

build = Builder(jenkins_job_name)
additional_properties = build.collect_property_files()
common.concatenate_files(additional_properties, f"../snapshot/{jenkins_job_name}.properties", True)
test_plan_abs_path = build.test_plan_abs(test_plan_base_dir)
test_plan = TestPlan(test_plan_abs_path)
test_plan.change_controller_type(test_plan_abs_path)
build.generate_new_build_xml(jenkins_job_workspace, jmeter_home, test_name, test_plan_base_dir, new_build_xml)
