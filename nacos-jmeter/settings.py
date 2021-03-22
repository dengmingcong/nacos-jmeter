import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_BASE = os.path.join(PROJECT_ROOT, "data")
COMMIT_HISTORY = os.path.join(DATA_BASE, "commit.log")
NACOS_SNAPSHOT_REPO_NAME = "nacos-snapshot"
NACOS_SNAPSHOT_REPO_DIR = f"d:/03 mp products/01 cg Git代码/nacos-snapshot"
NACOS_SNAPSHOT_REPO_URL = "git@fangcun.vesync.com:testTeam/nacos-snapshot.git"
NACOS_CLIENT_DEBUGGING = False

# Nacos server info
HOST_CI = "34.234.176.173"
HOST_TESTONLINE = "10.40.9.73"
HOST_PREDEPLOY = "10.40.9.73"
HOST_SIT = "10.40.9.73"
PORT = 8848

ANT_HOME = "d:/Program Files (x86)/apache-ant-1.9.15"
SUMMARY_EXTENSION_BEFORE_ENCODE = ".utf8"
SUMMARY_EXTENSION_AFTER_ENCODE = ".properties"

CROSS_ENV_NAMESPACE_ID = "cross-env"
# denote Jenkins job stage flag and the related namespace id.
STAGE_TO_NAMESPACE_IDS = {
    "ci": "env-01",
    "testonline": "env-02",
    "predeploy": "env-03",
    "production": "env-04"
}
SUMMARY_NAMESPACE_ID = ""

DEBUG_GROUP = "DEBUG"
# item that comes later in list has higher priority
STAGE_PRESET_GROUPS = ["SHARED", "DEVICE"]
SUMMARY_GROUP = "DEFAULT_GROUP"

SNAPSHOT_RULE_DATA_ID = "nacos.snapshot.rule"
SNAPSHOT_RULE_GROUP = "DEFAULT_GROUP"
SYNC_TRIGGER_DATA_ID = "nacos.commit.message"
SYNC_TRIGGER_GROUP = "DEFAULT_GROUP"

JENKINS_JMX_RELATIONSHIP_DATA_ID = "nacos.jmeter.test-plan"
JENKINS_JMX_RELATIONSHIP_GROUP = "DEFAULT_GROUP"
JENKINS_JMX_RELATIONSHIP_NAMESPACE_ID = ""

ON_SAMPLE_ERROR_ACTION = "stopthread"

