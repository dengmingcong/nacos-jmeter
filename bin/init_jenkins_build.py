import sys
sys.path.append("../nacos-jmeter")

from builder import Builder
from testplan import TestPlan

jenkins_job_name = sys.argv[1]
jenkins_job_workspace = sys.argv[2]
jmeter_home = sys.argv[3]
test_name = sys.argv[4]
test_plan_base_dir = sys.argv[5]
new_build_xml = sys.argv[6]

build = Builder(jenkins_job_name, jenkins_job_workspace, jmeter_home, test_name, test_plan_base_dir)
build.concatenate_property_files(f"../snapshot/{jenkins_job_name}.properties", True)
test_plan = TestPlan(build.test_plan_abs_path)
test_plan.change_controller_type(build.test_plan_abs_path)
build.generate_new_build_xml(new_build_xml)