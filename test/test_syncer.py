import settings
import syncer, nacosserver

if __name__ == "__main__":
    nacos_server = nacosserver.NacosServer(settings.NACOS_SERVER_HOST_CI, settings.NACOS_SERVER_PORT)
    s = syncer.NacosSyncer(nacos_server)
    s.run()
