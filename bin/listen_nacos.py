from pathlib import Path
import sys
sys.path.append("../nacos-jmeter")

from loguru import logger

import nacosserver
import settings
import syncer


if __name__ == "__main__":
    log_dir = settings.LOG_DIR
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logger.add(f"{log_dir}/" + "syncer_{time}.log", rotation="5 MB", compression="zip", encoding="utf-8")
    nacos_server = nacosserver.NacosServer(settings.HOST_TESTONLINE, settings.PORT)
    s = syncer.NacosSyncer(nacos_server)
    s.run()
