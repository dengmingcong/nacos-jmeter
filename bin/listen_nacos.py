import sys
sys.path.append("../nacos-jmeter")

import nacosserver
import settings
import syncer


if __name__ == "__main__":
    nacos_server = nacosserver.NacosServer(settings.HOST_TESTONLINE, settings.PORT)
    s = syncer.NacosSyncer(nacos_server)
    s.run()
