import settings
import syncer, nacosserver

if __name__ == "__main__":
    nacos_server = nacosserver.NacosServer(settings.HOST_CI, settings.PORT)
    s = syncer.NacosSyncer(nacos_server)
    s.run()
