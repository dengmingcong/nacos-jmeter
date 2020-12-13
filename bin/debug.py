import sys
sys.path.append("../nacos-jmeter")

from builder import Builder
from nacos import Nacos
import common
import settings


jenkins_job_name = "debug-fullTest-Core400SUSR-Cloud-API-Testonline"
update_snapshot = True

# update Nacos snapshot if set true
if update_snapshot:
    print("update Nacos snapshot")
    snapshot_dir = "../snapshot"
    host = settings.HOST_CI
    nacos_new = Nacos(host, settings.PORT)
    nacos_new.make_snapshot(snapshot_dir)

build = Builder(jenkins_job_name)
for test_plan in build.relative_path_test_plans:
    print("Collect properties for test plan: " + test_plan)
    additional_properties = build.collect_property_files(test_plan)
    common.concatenate_files(additional_properties, f"../snapshot/{jenkins_job_name}.properties", False)
