import itertools

message_list = [
    ["iOS", "安卓"],
    # 3.0.62 之前所有版本只支持 h5 跳转，不支持 app 原生跳转；3.0.62 同时支持
    # ["支持 h5 跳转", "不支持 h5 跳转", "支持 App 原生页面跳转", "不支持 App 原生页面跳转"],
    ["美国", "日本"],
    ["2.9.17", "3.0.0", "3.0.62"]
]

banner_list = [
    ["iOS", "安卓"],
    # 3.0.62 之前所有版本只支持 h5 跳转，不支持 app 原生跳转；3.0.62 同时支持
    # ["支持 h5 跳转", "不支持 h5 跳转", "支持 App 原生页面跳转", "不支持 App 原生页面跳转"],
    ["美国"],
    ["2.9.17", "3.0.62", "3.1.0"],
    ["用户已关闭 banner", "用户未关闭 banner"]
]

for element in itertools.product(*banner_list):
    print(element)