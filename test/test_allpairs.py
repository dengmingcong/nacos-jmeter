from allpairspy import AllPairs

push_message_params = [
    ["os=iOS", "os=安卓"],
    ["msgType=h5 跳转", "msgType=原生页面跳转"],
    ["pushCountry=美国"],
    ["basicsAppVersion=all", "basicsAppVersion=2.9.17", "basicsAppVersion=3.0.0", "basicsAppVersion=3.0.62"],
    ["highBasicsAppVersion=true", "highBasicsAppVersion=false"],
    ["targetAccountIdsObtaining=所有用户", "targetAccountIdsObtaining=单个用户", "targetAccountIdsObtaining=多个用户"]
]

push_banner_params = [
    # app_configurations 可以看出，只有 home 支持关闭 banner，所以这个选项和后面的关闭 banner 有冲突，去掉
    # ["showPosition=home", "showPosition=smart", "showPosition=more"],
    ["os=iOS", "os=安卓"],
    ["pageJumpMode=h5 跳转", "pageJumpMode=原生页面跳转"],
    # 是否支持创建 banner 只决定构造用户，不决定配置
    # ["支持创建 banner", "不支持创建 banner"],
    ["bannerShowCountry=美国"],
    ["basicsAppVersion=all", "basicsAppVersion=2.9.17", "basicsAppVersion=3.0.62", "basicsAppVersion=3.1.0"],
    ["highBasicsAppVersion=true", "highBasicsAppVersion=false"],
    ["targetAccountIdsObtaining=所有用户", "targetAccountIdsObtaining=单个用户", "targetAccountIdsObtaining=多个用户"],
    ["用户已关闭 banner", "用户未关闭 banner"],
    ["turnOnSwitchFlag=true", "turnOnSwitchFlag=false"]
]

push_banner_target_user_count_params = [
    # app_configurations 可以看出，只有 home 支持关闭 banner，所以这个选项和后面的关闭 banner 有冲突，去掉
    # ["showPosition=home", "showPosition=smart", "showPosition=more"],
    ["os=iOS", "os=安卓"],
    ["pageJumpMode=h5 跳转", "pageJumpMode=原生页面跳转"],
    # 是否支持创建 banner 只决定构造用户，不决定配置
    # ["支持创建 banner", "不支持创建 banner"],
    ["bannerShowCountry=美国"],
    ["basicsAppVersion=all", "basicsAppVersion=2.9.17", "basicsAppVersion=3.0.62", "basicsAppVersion=3.1.0"],
    ["highBasicsAppVersion=true", "highBasicsAppVersion=false"],
    ["targetAccountIdsObtaining=所有用户"],
    ["turnOnSwitchFlag=true", "turnOnSwitchFlag=false"]
]

# for i, pairs in enumerate(AllPairs(push_message_params)):
#     print("{:2d}: {}".format(i, pairs))

for i, pairs in enumerate(AllPairs(push_banner_target_user_count_params)):
    print("{:2d}: {}".format(i, pairs))
