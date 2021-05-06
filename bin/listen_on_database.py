from os import path
from pathlib import Path
import sys
project_root = path.dirname(path.dirname(path.abspath(__file__)))
sys.path.append(f"{project_root}/nacos-jmeter")

from loguru import logger

import nacosserver
import settings
import syncer


if __name__ == "__main__":
    log_dir = settings.LOG_DIR
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logger.add(f"{log_dir}/" + "database_syncer_{time}.log", rotation="5 MB", compression="zip", encoding="utf-8",
               level="INFO")
    nacos_server = nacosserver.NacosServer(settings.HOST_CI, settings.PORT)
    s = syncer.DatabaseSyncer("ci", nacos_server)
    s.run()
