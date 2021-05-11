from deepdiff import DeepDiff
from pprint import pprint
import yaml

t1 = {1:1, 3:3, 2:2, 4:{"a":"hello", "b":[1, 2, 3]}}
t2 = {1:1, 2:2, 3:3, 4:{"a":"hello", "b":[1, 2, 3, 2]}}

t3 = """
10AOutletEU:
  category: wifi-switch
  config_model: 10AOutletEU
  detail_table_name: device_detail_wifi_switch
  device_brand: etekcity
  device_img: https://image.vesync.com/defaultImages/ESW01_EU/icon_10a_wifi_outlet_80.png
  model: ESW01-EU
  model_img: https://image.vesync.com/defaultImages/ESW01_EU/icon_10a_wifi_outlet_160.png
  model_name: Etekcity 10A WiFi Outlet Europe
  type: wifi-switch
  typeV2: outlet
10AOutletUS:
  category: wifi-switch
  config_model: 10AOutletUS
  detail_table_name: device_detail_wifi_switch
  device_brand: etekcity
  device_img: https://image.vesync.com/defaultImages/ESW01_USA_Series/icon_7a_outlet_80.png
  model: ESW03-USA
  model_img: https://image.vesync.com/defaultImages/ESW01_USA_Series/icon_7a_wifi_outlet_160.png
  model_name: Etekcity 10A WiFi Outlet
  type: wifi-switch
  typeV2: outlet
"""

t4 = """
10AOutletEU:
  category: wifi-switches
  config_model: 10AOutletEU
  detail_table_name: device_detail_wifi_switch
  device_brand: etekcity
  device_img: https://image.vesync.com/defaultImages/ESW01_EU/icon_10a_wifi_outlet_80.png
  model: ESW01-EU
  model_img: https://image.vesync.com/defaultImages/ESW01_EU/icon_10a_wifi_outlet_160.png
  model_name: Etekcity 10A WiFi Outlet Europe
  type: wifi-switch
  typeV2: outlet
10AOutletUS:
  category: wifi-switch
  config_model: 10AOutletUS
  detail_table_name: device_detail_wifi_switch
  device_brand: etekcity
  device_img: https://image.vesync.com/defaultImages/ESW01_USA_Series/icon_7a_outlet_80.png
  model: ESW03-USA
  model_img: https://image.vesync.com/defaultImages/ESW01_USA_Series/icon_7a_wifi_outlet_160.png
  model_name: Etekcity 10A WiFi Outlet
  type: wifi-switch
  typeV2: outlet
abc:
    abc: def
"""
t3 = yaml.safe_load(t3)
t4 = yaml.safe_load(t4)
t = {}
ddiff = DeepDiff(t3, t4)
print(len(ddiff))
print(ddiff.pretty())