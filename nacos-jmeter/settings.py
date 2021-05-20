from os import path

PROJECT_ROOT = path.dirname(path.dirname(path.abspath(__file__)))
LOG_DIR = "/var/log/nacos-syncer"
DATA_BASE = path.join(PROJECT_ROOT, "data")
COMMIT_HISTORY = path.join(DATA_BASE, "commit.log")
NACOS_SNAPSHOT_REPO_NAME = "nacos-snapshot"
# for syncer only, in most case cannot be used as snapshot_base of builder
NACOS_SNAPSHOT_REPO_DIR = f"/data/qa/{NACOS_SNAPSHOT_REPO_NAME}"
NACOS_SNAPSHOT_REPO_URL = "git@fangcun.vesync.com:testTeam/nacos-snapshot.git"
NACOS_CLIENT_DEBUGGING = False

JMETER_HOME = "d:/Program Files (x86)/apache-jmeter-5.4.1"

# Nacos server info
NACOS_SERVER_HOST_CI = "34.234.176.173"
NACOS_SERVER_HOST_TESTONLINE = "10.40.9.73"
NACOS_SERVER_HOST_PREDEPLOY = "10.40.9.73"
NACOS_SERVER_HOST_SIT = "10.40.9.73"
NACOS_SERVER_PORT = 8848

SUMMARY_EXTENSION_BEFORE_ENCODE = ".utf8"
SUMMARY_EXTENSION_AFTER_ENCODE = ".properties"

# namespaces
CROSS_ENV_NAMESPACE_ID = "cross-env"
# denote Jenkins job stage flag and the related namespace id.
STAGE_TO_NAMESPACE_IDS = {
    "ci": "env-01",
    "testonline": "env-02",
    "predeploy": "env-03",
    "production": "env-04"
}
SUMMARY_NAMESPACE_ID = "summary"
JENKINS_JMX_RELATIONSHIP_NAMESPACE_ID = ""

# groups
DEBUG_GROUP = "DEBUG"
# item that comes later in list has higher priority
STAGE_PRESET_GROUPS = ["SHARED", "DEVICE"]
SUMMARY_GROUP_DEBUG = "DEBUG"
SUMMARY_GROUP_STABLE = "STABLE"
SYNC_TRIGGER_GROUP = "DEFAULT_GROUP"
JENKINS_JMX_RELATIONSHIP_GROUP = "DEFAULT_GROUP"
VESYNC_DATABASE_GROUP = "SHARED"
DATABASE_SNAPSHOT_GROUP = "DATABASE"

# data ids
SYNC_TRIGGER_DATA_ID = "nacos.commit.message"
JENKINS_JMX_RELATIONSHIP_DATA_ID = "nacos.jmeter.test-plan"
VESYNC_DATABASE_DATA_ID = "common"
TABLE_DEVICE_TYPE_DATA_ID = "vesync-main.device-type"
TABLE_FIRMWARE_INFO_DATA_ID = "vesync-main.firmware-info"

# configs
KEY_TO_VESYNC_DATABASE_HOST = "cloud.service.database.host"
KEY_TO_VESYNC_DATABASE_PORT = "cloud.service.database.port"
KEY_TO_VESYNC_DATABASE_USER = "cloud.service.database.user"
KEY_TO_VESYNC_DATABASE_PASSWORD = "cloud.service.database.password"
KEY_TO_VESYNC_DATABASE_NAME = "cloud.service.database.name"

ON_SAMPLE_ERROR_ACTION = "stopthread"
DATABASE_SYNCER_INTERVAL = 60
