import datetime
import decimal
import yaml

import dictdiffer
import nacos
import pymysql
from dingtalkchatbot.chatbot import DingtalkChatbot


class DingTalkRobot(object):
    def __init__(self, webhook):
        self.webhook = webhook
        self.msg = ""
        self.at_mobiles = []
        self.dingRobort = DingtalkChatbot(self.webhook)

    def setParameter(self, msg):
        self.msg = "test:" + msg
        # self.at_mobiles = at_mobiles

    def sendMessage(self):
        self.dingRobort.send_text(self.msg)


def get_config_info(data_id, group, namespace):
    SERVER_ADDRESSES = "34.234.176.173"
    NAMESPACE = namespace
    client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE, username="nacos", password="nacos")
    common_db = client.get_config(data_id, group)
    common_db = yaml.safe_load(common_db)
    return common_db


def DB(db_name, sql):
    '''
    连接mysql数据库
    :param sql: 传sql语句
    :return: 数据库结果
    '''
    common_db = get_config_info("common.db","SHARED","env-01")
    db_ip = common_db.get("cloud.service.db.ip")
    db_user = common_db.get("cloud.service.db.user")
    db_pwd = common_db.get("cloud.service.db.password")
    port = common_db.get("cloud.service.db.port")
    conn = pymysql.connect(host=db_ip, user=db_user, passwd=db_pwd, db=db_name, port=port, charset='utf8',
                           cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    result = cursor.fetchall()
    return result


def DB_dict(db_name, sql):
    '''
    数据库查询，返回接口驼峰命名的字典，用于和其他接口匹配
    :param sql 传查询语句
    '''
    select_result_dict_list = []
    select_result_dict = DB(db_name, sql)
    for select_result in select_result_dict:
        new_dict = select_result
        for i in list(new_dict.keys()):
            if '_' in i:
                new_i_list = []
                for j, k in enumerate(i.split('_')):
                    if j > 0:
                        k = str(k).capitalize()
                    new_i_list.append(k)
                new_key = ''.join(new_i_list)
                if type(select_result[i]) == datetime.datetime:
                    select_result[new_key] = select_result[i].strftime('%Y-%m-%d %H:%M:%S')
                elif type(select_result[i]) == datetime.date:
                    select_result[new_key] = select_result[i].strftime('%Y-%m-%d')
                elif type(select_result[i]) == decimal.Decimal:
                    select_result[new_key] = float(select_result[i])
                else:
                    select_result[new_key] = select_result[i]
                del select_result[i]
            else:
                new_key = i
                if type(select_result[i]) == datetime.datetime:
                    select_result[new_key] = select_result[i].strftime('%Y-%m-%d %H:%M:%S')
                elif type(select_result[i]) == datetime.date:
                    select_result[new_key] = select_result[i].strftime('%Y-%m-%d')
                elif type(select_result[i]) == decimal.Decimal:
                    select_result[new_key] = float(select_result[i])
                else:
                    select_result[new_key] = select_result[i]
        select_result_dict_list.append(select_result)
    return select_result_dict_list


def get_dict_byConfigModel():
    # 查询device_type表
    sql = "SELECT type,model,model_img,model_name,device_img,config_model,detail_table_name,device_brand,typeV2,category FROM device_type"

    # 返回结果集，是列表
    device_type_list = DB_dict('vesync_main', sql)

    # 定义一个字典，存新的字典
    device_type_dict = {}

    # 将列表转换为以configModel为key，其他键值对为value的新字典
    for i in device_type_list:
        device_type_dict_sub = {}
        device_type_dict_sub["type"] = i.get("type")
        device_type_dict_sub["model"] = i.get("model")
        device_type_dict_sub["typeV2"] = i.get("typeV2")
        device_type_dict_sub["modelImg"] = i.get("modelImg")
        device_type_dict_sub["modelName"] = i.get("modelName")
        device_type_dict_sub["deviceImg"] = i.get("deviceImg")
        device_type_dict_sub["detailTableName"] = i.get("detailTableName")
        device_type_dict_sub["deviceBrand"] = i.get("deviceBrand")
        device_type_dict[i.get("configModel")] = device_type_dict_sub
    # print(device_type_dict)

    return device_type_dict


def get_dict_byFirmware():
    # 查询firmware_info表
    sql = "SELECT f1.config_module,f1.firmware_version,f1.device_region,f1.firmware_url FROM firmware_info AS f1 " \
          "INNER JOIN ( SELECT max( version_code ) AS max_version_code, config_module,device_region,plugin_name  FROM " \
          "firmware_info AS f2  GROUP BY f2.config_module,f2.device_region, f2.plugin_name ) AS f3 ON f1.version_code " \
          "= f3.max_version_code AND f1.config_module = f3.config_module  AND f1.device_region = f3.device_region  " \
          "AND f1.plugin_name = f3.plugin_name "
        # 返回结果集，是列表
    firmwareInfo_list = DB_dict('vesync_main', sql)

    # 定义一个字典，存新的字典
    firmwareInfo_dict = {}

    # 将列表转换为以configModel为key，其他键值对为value的新字典
    for i in firmwareInfo_list:
        firmwareInfo_dict_sub = {}
        firmwareInfo_dict_sub["deviceRegion"] = i.get("deviceRegion")
        firmwareInfo_dict_sub["pluginName"] = i.get("pluginName")
        firmwareInfo_dict_sub["firmwareUrl"] = i.get("firmwareUrl")
        firmwareInfo_dict_sub["firmwareInfo"] = i.get("firmwareInfo")
        firmwareInfo_dict[i.get("configModule")] = firmwareInfo_dict_sub
    # print(firmwareInfo_dict)

    return firmwareInfo_dict


def ifDeviceTypeHasChanged():
    SERVER_ADDRESSES = "34.234.176.173"
    NAMESPACE = "env-01"
    client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE, username="nacos", password="nacos")
    data_id = "device.properties.deviceType"
    group = "DEVICE"
    changed_list = []
    configResult = client.get_config(data_id,group)
    if configResult is None:
        device_type_dict = get_dict_byConfigModel()
        device_type_dict = yaml.dump(device_type_dict)
        client.publish_config(data_id, group, device_type_dict)

    elif configResult is not None:
        configResult = yaml.safe_load(configResult)
        device_type_dict_2 = get_dict_byConfigModel()
        for diff in list(dictdiffer.diff(configResult, device_type_dict_2)):
            # print(diff)
            changed_list.append(diff)
    if len(changed_list) != 0:
        print(len(changed_list))
        device_type_dict = yaml.dump(device_type_dict_2)
        client.publish_config(data_id, group, device_type_dict)
        m_test = DingTalkRobot(
            'https://oapi.dingtalk.com/robot/send?access_token=bfe75c087830cdd46c321c5723c7706bec56fe261f6b6900dbf33a02b7ce9724')
        m_test.setParameter(f"{changed_list}")
        m_test.sendMessage()
    return changed_list


def ifFirmwareInfoHasChanged():
    SERVER_ADDRESSES = "34.234.176.173"
    NAMESPACE = "env-01"
    client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE, username="nacos", password="nacos")
    data_id = "device.properties.firmwareInfo"
    group = "DEVICE"
    changed_list = []
    configResult = client.get_config(data_id,group)
    if configResult is None:
        device_type_dict = get_dict_byFirmware()
        device_type_dict = yaml.dump(device_type_dict)
        client.publish_config(data_id, group, device_type_dict)

    elif configResult is not None:
        configResult = yaml.safe_load(configResult)
        device_type_dict_2 = get_dict_byFirmware()
        for diff in list(dictdiffer.diff(configResult, device_type_dict_2)):
            # print(diff)
            changed_list.append(diff)
    if len(changed_list) != 0:
        device_type_dict = yaml.dump(device_type_dict_2)
        client.publish_config(data_id, group, device_type_dict)
        m_test = DingTalkRobot(
            'https://oapi.dingtalk.com/robot/send?access_token=bfe75c087830cdd46c321c5723c7706bec56fe261f6b6900dbf33a02b7ce9724')
        m_test.setParameter(f"{changed_list}")
        m_test.sendMessage()
    return changed_list


print(ifDeviceTypeHasChanged())
print(ifFirmwareInfoHasChanged())