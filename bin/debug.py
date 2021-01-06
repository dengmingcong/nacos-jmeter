import os
import sys
sys.path.append("../nacos-jmeter")

from builder import Builder
from snapshot import Nacos
import common
import settings


jenkins_job_name = "fullTest-Core400SUS-Cloud-API-CI"
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
    test_plan_file_name = os.path.splitext(os.path.basename(test_plan))[0]
    print("Collect properties for test plan: " + test_plan)
    additional_properties = build.collect_property_files(test_plan)
    concatenated_property_file = f"../snapshot/{test_plan_file_name}-{build.stage}.properties"
    common.concatenate_files(additional_properties, concatenated_property_file, False)
