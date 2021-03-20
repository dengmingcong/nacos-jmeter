import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

# Nacos server info
HOST_CI = "34.234.176.173"
HOST_TESTONLINE = "10.40.9.73"
HOST_PREDEPLOY = "10.40.9.73"
HOST_SIT = "10.40.9.73"
PORT = 8848

SNAPSHOT_RULE_DATA_ID = "nacos.snapshot.rule"
SNAPSHOT_RULE_GROUP = "DEFAULT_GROUP"
SYNC_TRIGGER_DATA_ID = "nacos.commit.message"
SYNC_TRIGGER_GROUP = "DEFAULT_GROUP"

JENKINS_JMX_RELATIONSHIP_DATA_ID = "nacos.jmeter.test-plan"
JENKINS_JMX_RELATIONSHIP_GROUP = "DEFAULT_GROUP"

ON_SAMPLE_ERROR_ACTION = "stopthread"

DATA_BASE = os.path.join(PROJECT_ROOT, "data")
COMMIT_HISTORY = os.path.join(DATA_BASE, "commit.log")
NACOS_SNAPSHOT_REPO_NAME = "nacos-snapshot"
NACOS_SNAPSHOT_REPO_DIR = f"d:/03 mp products/01 cg Git代码/{NACOS_SNAPSHOT_REPO_NAME}"
NACOS_SNAPSHOT_REPO_URL = "git@fangcun.vesync.com:testTeam/nacos-snapshot.git"
NACOS_CLIENT_DEBUGGING = False
