from allpairspy import AllPairs

push_message_params = [
    ["os=iOS", "os=安卓"],
    ["msgType=h5 跳转", "msgType=原生页面跳转"],
    ["pushCountry=美国"],
    ["basicsAppVersion=all", "basicsAppVersion=2.9.17", "basicsAppVersion=3.0.0", "basicsAppVersion=3.0.62"],
    ["highBasicsAppVersion=true", "highBasicsAppVersion=false"],
    ["targetAccountIdsObtaining=所有用户"]
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
    ["targetAccountIdsObtaining=所有用户"],
    # 只作为构造用户的因素
    # ["用户已关闭 banner", "用户未关闭 banner"],
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

# 目的是哪些用户可以收到 banner，所以位置不放在这儿
push_banner_to_mall_params_old = [
    ["投放系统=全部", "投放系统=Android", "投放系统=iOS"],
    ["投放用户=所有用户", "投放用户=成交用户", "投放用户=未成交用户", "投放用户=指定用户"],
]

# 只考虑 app 端是否能拉取到 banner 数据
push_banner_to_mall_params_new = [
    ["投放用户=所有用户", "投放用户=成交用户", "投放用户=未成交用户"],
    ["投放终端=Android", "投放终端=iOS", "投放终端=PC", "投放终端=M"],
    ["跳转链接=商品详情页", "跳转链接=原生页面", "跳转链接=自定义 H5 页面", "跳转链接=无"],
    ["App 版本=所有版本", "App 版本=最低支持商城的版本", "App 版本=最低支持原生跳转的版本"],
    ["是否高于=是", "是否高于=否"]
]

banner_switch = [
    ["未到展示时间", "在展示时间之内", "已过展示时间"],
    ["状态=关闭，可以成功打开，打开后", "状态=打开，可以成功关闭，关闭后", "状态=关闭", "状态=打开"],
]

new_coupon_params = [
    ["coupon 类型=按百分比折扣", "coupon 类型=按金额直减"],
    ["优惠额度=有门槛", "优惠额度=无门槛"],
    ["可使用次数=限制次数", "可使用次数=不限次数"],
    ["每人可使用次数=限制次数", "每人可使用次数=不限次数"],
    ["指定商品=按分类", "指定商品=按商品"],
    ["指定用户=指定用户可用", "指定用户=所有用户可用"]
]

# for i, pairs in enumerate(AllPairs(push_message_params)):
#     print("{:2d}: {}".format(i, pairs))

for i, pairs in enumerate(AllPairs(push_banner_to_mall_params_new)):
    common_expect = ""
    pairs = ", ".join(pairs)
    print(f"P-{pairs}{common_expect}")
