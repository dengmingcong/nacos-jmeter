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

mall_banner_list_old = [
    ["iOS", "安卓"],
    ["新用户", "老用户"],
]

mall_banner_list_new = [
    ["有成交记录的商城用户", "无成交记录的商城用户", "游客"],
    ["登录终端=android, App 版本=最低支持商城的版本", "登录终端=android, App 版本=最低支持原生页面跳转的版本",
     "登录终端=iOS, App 版本=最低支持商城的版本", "登录终端=iOS, App 版本=最低支持原生页面跳转的版本",
     "登录终端=PC", "登录终端=M"],
]

app_version = [
    ["VeSync ", "v"],
    ["3.1.2", "3.1.6"],
    [" build2", "-build2", ""],
]

for element in itertools.product(*app_version):
    print("".join(element))