import nacos
import settings

SERVER_ADDRESSES = f"{settings.HOST_CI}"
NAMESPACE = "env-01"

# no auth mode
client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE)
# client.set_options(no_snapshot=True)
# auth mode
#client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE, username="nacos", password="nacos")

# get config
data_id = "common"
group = "SHARED"
print(client.get_configs())
