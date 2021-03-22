import os
import subprocess
import sys
sys.path.append("../nacos-jmeter")

import nacos

import settings


if __name__ == "__main__":
    # choose one from "ci", "testonline", "predeploy", "production"
    stage = "ci"

    snapshot_base = os.path.join(settings.JMETER_HOME, "bin")

    # get summary configs for specific stage
    nacos_client = nacos.NacosClient(settings.HOST_CI, namespace=settings.SUMMARY_NAMESPACE_ID)
    nacos_client.set_options(snapshot_base=snapshot_base)
    nacos_client.get_config(stage, settings.SUMMARY_GROUP)

    # rename summary config file
    os.chdir(snapshot_base)
    old_file = "+".join([stage, settings.SUMMARY_GROUP, settings.SUMMARY_NAMESPACE_ID])
    new_file = f"{stage}.properties"
    os.rename(old_file, new_file)

    # start JMeter with additional properties
    subprocess.run(f"jmeter -q {new_file}", shell=True)
