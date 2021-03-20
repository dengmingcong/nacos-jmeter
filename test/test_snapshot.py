import os
import settings
import syncer

if __name__ == "__main__":
    s = syncer.NacosSyncer(settings.HOST_CI, settings.PORT, settings.NACOS_CLIENT_DEBUGGING)
    s.run()
