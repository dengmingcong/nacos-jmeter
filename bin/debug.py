import os
import subprocess
import sys
root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(f"{root}/nacos-jmeter")

from loguru import logger
import nacos

import settings


if __name__ == "__main__":
    # choose one from "ci", "testonline", "predeploy", "production"
    stage = "ci"
    debug = True

    snapshot_base = os.path.join(settings.JMETER_HOME, "bin")
    logger.info(f"snapshot base is set to {snapshot_base}")

    # get summary configs for specific stage
    nacos_client = nacos.NacosClient(settings.HOST_CI, namespace=settings.SUMMARY_NAMESPACE_ID)
    nacos_client.set_options(snapshot_base=snapshot_base)
    summary_group = settings.SUMMARY_GROUP_DEBUG if debug else settings.SUMMARY_GROUP_STABLE
    nacos_client.get_config(stage, summary_group)

    # rename summary config file
    os.chdir(snapshot_base)
    old_file = "+".join([stage, summary_group, settings.SUMMARY_NAMESPACE_ID])
    new_file = f"{stage}.properties"

    # check if get config file successfully
    if os.path.isfile(old_file):
        # delete if already exist
        if os.path.isfile(new_file):
            os.remove(new_file)
        os.rename(old_file, new_file)
        # start JMeter with additional properties
        logger.info(f"start JMeter with property file {snapshot_base}/{new_file} loaded")
        subprocess.run(f"jmeter -q {new_file}", shell=True)
    else:
        if os.path.isfile(new_file):
            logger.warning("Nacos 服务好像挂了，无法拿到最新的配置，加载之前的配置文件来启动 JMeter")
            # start JMeter with additional properties
            logger.info(f"start JMeter with property file {snapshot_base}/{new_file} loaded")
            subprocess.run(f"jmeter -q {new_file}", shell=True)
        else:
            logger.error("Nacos 服务好像挂了，无法拿到最新的配置")
