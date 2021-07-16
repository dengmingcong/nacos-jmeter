import itertools

message_list = [
    ["iOS", "安卓"],
    # 3.0.62 之前所有版本只支持 h5 跳转，不支持 app 原生跳转；3.0.62 同时支持
    # ["支持 h5 跳转", "不支持 h5 跳转", "支持 App 原生页面跳转", "不支持 App 原生页面跳转"],
    ["美国", "加拿大", "德国", "阿根廷"],
    ["2.9.17", "3.0.62", "3.1.18"]
]

banner_list = [
    ["iOS", "安卓"],
    # 3.0.62 之前所有版本只支持 h5 跳转，不支持 app 原生跳转；3.0.62 同时支持
    # ["支持 h5 跳转", "不支持 h5 跳转", "支持 App 原生页面跳转", "不支持 App 原生页面跳转"],
    ["美国", "越南", "阿根廷"],
    ["2.9.17", "3.0.62", "3.1.18"],
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


push_sprint_two_creator_params = [
    ["创建人=对外运营经理", "创建人=对内运营经理", "创建人=一级审核人员", "创建人=二级审核人员"],
    ["推送用户范围=单个用户", "推送用户范围=用户群", "推送用户范围=全量"],
    ["状态=草稿", "状态=一级审核中", "状态=二级审批中", "状态=三级审批中", "状态=审批不通过", "状态=待发送"],
]

push_sprint_two_approver_params = [
    ["创建人=对外运营经理", "创建人=对内运营经理", "创建人=一级审核人员", "创建人=二级审核人员"],
    ["推送用户范围=单个用户", "推送用户范围=用户群", "推送用户范围=全量"],
    ["状态=草稿", "状态=一级审核中", "状态=二级审批中", "状态=三级审批中", "状态=审批不通过", "状态=待发送"],
]

push_sprint_two_to_be_approved_params = [
    ["创建人=对外运营经理", "创建人=对内运营经理", "创建人=一级审核人员", "创建人=二级审核人员"],
    ["推送用户范围=用户群", "推送用户范围=全量"],
    ["状态=一级审核中", "状态=二级审批中", "状态=三级审批中"],
]

push_sprint_two_preview_params = [
    ["创建人=对外运营经理", "创建人=对内运营经理", "创建人=一级审核人员", "创建人=二级审核人员"],
    ["推送用户范围=单个用户", "推送用户范围=用户群", "推送用户范围=全量"],
]

for element in itertools.product(*banner_list):
    print(",".join(element))
