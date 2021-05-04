from dingtalkchatbot.chatbot import DingtalkChatbot

access_token = "c8a9d345d0f37a99cf72af8d58a3984409161efa4350c437acf02e31443c90db"
webhook = f"https://oapi.dingtalk.com/robot/send?access_token={access_token}"
robot = DingtalkChatbot(webhook)

#robot.send_text(msg="DB: 测试 @ 某一个人", at_mobiles=[18380217140])
robot.send_markdown(title='DB: 数据库变化', text="- **Type**: change, "
                                            "**Device**: 10AOutletEU.firmwareUrl, "
                                            "**Before**: http://firm-online.vesync.com:4005/firm/amazon/10AOutletEU/v1.0.07/, "
                                            "**After**: http://54.222.135.96:4005/firm/amazon/10AOutletEU/v1.1.19/",
                    is_at_all=True)
