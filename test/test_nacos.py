import nacos
import settings

SERVER_ADDRESSES = f"{settings.NACOS_SERVER_HOST_CI}"
NAMESPACE = "env-01"

namespace_id = ""
data_id = "ci"
group = "DEFAULT_GROUP"
# no auth mode
client = nacos.NacosClient("127.0.0.1", namespace=namespace_id)
# client.set_options(no_snapshot=True)
# auth mode
#client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE, username="nacos", password="nacos")

# get config
with open("../snapshot/core400s+DEVICE+env-01", "r") as in_file:
    s = in_file.read()
    client.publish_config(data_id, group, content=s)
