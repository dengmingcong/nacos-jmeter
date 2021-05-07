from nacosserver import NacosServer
import settings

ns = NacosServer(settings.NACOS_SERVER_HOST_CI, 8838)
