import os
import subprocess
import sys
sys.path.append("../nacos-jmeter")

import nacos

import settings


if __name__ == "__main__":
    # one of "ci", "testonline", "predeploy", "production"
    stage = "ci"

    # get summary configs for specific stage
    snapshot_base = os.path.join(settings.JMETER_HOME, "bin")
    nacos_client = nacos.NacosClient(settings.HOST_CI, namespace=settings.SUMMARY_NAMESPACE_ID)
    nacos_client.set_options(snapshot_base=snapshot_base)
    nacos_client.get_config(stage, settings.SUMMARY_GROUP)

    # rename summary config file
    summary_file_name = "+".join([stage, settings.SUMMARY_GROUP, settings.SUMMARY_NAMESPACE_ID])
    os.chdir(snapshot_base)
    old_file = summary_file_name
    new_file = f"{stage}.properties"
    os.rename(old_file, new_file)

    # start JMeter with additional properties
    subprocess.run(["jmeter", "-q", new_file])
