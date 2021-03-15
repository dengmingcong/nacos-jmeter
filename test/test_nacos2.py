import sys
sys.path.append("../nacos-jmeter")
import time
import nacos
import settings

#SERVER_ADDRESSES = "localhost"
SERVER_ADDRESSES = f"{settings.HOST_CI}"
NAMESPACE = "env-01"

# no auth mode
client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE)
# auth mode
#client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE, username="nacos", password="nacos")

# get config
data_id = "WiFiBTOnboardingNotify_AirPurifier_LAP-C401S-WUSR_US"
group = "DEVICE"


def println(params):
    print(f"{params['data_id']}hello, properties changes detected.")


if __name__ == "__main__":
    client.set_debugging()
    # client.get_config(data_id, group)
    for i in range(10):
        client.add_config_watcher(data_id, group, println)
    time.sleep(10000)