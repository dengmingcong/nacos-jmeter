import nacos

SERVER_ADDRESSES = "127.0.0.1"
NAMESPACE = "cross-env"

# no auth mode
client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE)
# auth mode
#client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE, username="nacos", password="nacos")

# get config
data_id = "common"
group = "SHARED"
print(client.get_config(data_id, group))
