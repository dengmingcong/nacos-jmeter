from multiprocessing import Pool
import os, time, random
import sys
sys.path.append("../nacos-jmeter")
import time
import nacos
import settings

#SERVER_ADDRESSES = "localhost"
SERVER_ADDRESSES = f"{settings.NACOS_SERVER_HOST_CI}"
NAMESPACE = "env-01"

# no auth mode
client = nacos.NacosClient(SERVER_ADDRESSES)
# auth mode
#client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE, username="nacos", password="nacos")

# get config
data_id = "nacos.commit.message"
group = "DEFAULT_GROUP"


def println(params):
    print(f"{params['data_id']}hello, properties changes detected.")

def long_time_task(name):
    print(f"Run task {name} ({os.getpid()})")
    start = time.time()
    time.sleep(random.random() * 7)
    end = time.time()
    print(f"Task {name} runs {end - start} seconds.")

def test_multi(params):
    print(f"Parent process {os.getpid()}.")
    p = Pool()
    for i in range(5):
        p.apply_async(long_time_task, args=(i,))
    print("Waiting for all subprocesses done...")
    p.close()
    p.join()
    print('All subprocesses done.')

if __name__ == "__main__":
    client.set_debugging()
    # client.get_config(data_id, group)
    client.add_config_watcher(data_id, group, test_multi)
    time.sleep(10000)
