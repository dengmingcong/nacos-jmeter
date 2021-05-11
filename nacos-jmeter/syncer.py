from multiprocessing import Pool
from pathlib import Path
import datetime
import glob
import os
import time
import tempfile
import yaml

from deepdiff import DeepDiff
from dictdiffer import diff
from dingtalkchatbot.chatbot import DingtalkChatbot
from loguru import logger
from nacos.exception import NacosRequestException
from pymysqlpool import ConnectionPool
import git
import nacos
import pymysql

import common
import settings
from nacosserver import NacosServer
from collector import Collector


class NacosSyncer(object):
    """Class representing syncer from Nacos to git."""
    def __init__(self, nacos_server: NacosServer, nacos_client_debug=False):
        """Init class."""
        self.nacos_server = nacos_server

        self.index = []  # tasks staged (borrow the concept of git)
        self.sync_task_lock = False  # True if one sync task (make snapshot and push to git remote) is running
        self.sync_task_reason = ""

        self.nacos_snapshot_repo_url = settings.NACOS_SNAPSHOT_REPO_URL
        self.nacos_snapshot_repo_dir = settings.NACOS_SNAPSHOT_REPO_DIR
        self.nacos_snapshot_repo = self._init_nacos_snapshot_repo()

        self.commit_history_file = settings.COMMIT_HISTORY
        self.sync_trigger_data_id = settings.SYNC_TRIGGER_DATA_ID
        self.sync_trigger_group = settings.SYNC_TRIGGER_GROUP
        self.nacos_client_debug = nacos_client_debug

        self.stage_to_namespace_ids = settings.STAGE_TO_NAMESPACE_IDS
        self.summary_namespace_id = settings.SUMMARY_NAMESPACE_ID
        self.summary_group_debug = settings.SUMMARY_GROUP_DEBUG
        self.summary_group_stable = settings.SUMMARY_GROUP_STABLE

    def _init_nacos_snapshot_repo(self) -> git.Repo:
        """
        Returns an instance of git.Repo

        Returns:
            instance of git.Repo
        """
        if not os.path.exists(self.nacos_snapshot_repo_dir):
            git.Repo.clone_from(self.nacos_snapshot_repo_url, self.nacos_snapshot_repo_dir)
        return git.Repo(self.nacos_snapshot_repo_dir)

    def set_nacos_client_debug(self, client: nacos.NacosClient):
        """Enable NacosClient debugging when possible."""
        if self.nacos_client_debug:
            client.set_debugging()

    def download_one_namespace_configs(self, namespace_id, namespace_name, namespace_config_count, snapshot_base):
        """
        Download all configs of specific namespace.

        Args:
            namespace_id: id of namespace, passed when initializing NacosClient.
            namespace_name: name of namespace, used for logging.
            namespace_config_count: count of configs, passed as page size.
            snapshot_base: Dir to store snapshot config files.

        Returns:
            None
        """
        nacos_client = nacos.NacosClient(self.nacos_server.host, namespace=namespace_id)
        self.set_nacos_client_debug(nacos_client)
        nacos_client.set_options(snapshot_base=snapshot_base)
        logger.info(f"Begin to get configs from namespace: {namespace_name}")
        nacos_client.get_configs(page_size=namespace_config_count)
        logger.success(f"Succeed to get configs from namespace: {namespace_name}")

    def make_snapshot(self, snapshot_base, clean_base=False):
        """
        Download all configurations of every namespace to local in parallel.

        Files with the same name will be overwritten.
        Set clean_base to True if want to track configs deleted.

        :param snapshot_base: Dir to store snapshot config files, whose parent directory is named with 'nacos-snapshot'.
        :param clean_base: Remove all file in base before download from Nacos if set as True.
        """
        if clean_base:
            logger.debug("Parameter 'clean_base' was set to True, delete all files in base now.")
            files = glob.glob(f"{snapshot_base}/*")
            for f in files:
                os.remove(f)
        logger.info("Begin to make snapshot of Nacos.")
        # Note:
        #   When running in Windows, if another change occurs when handling current change, the process will always wait
        #   nearly one minute and I don't know why, but in macOS, it works great.
        #   If running on Linux this happens, log pid to try to find reason.
        namespaces = self.nacos_server.get_namespaces()
        p = Pool(len(namespaces))
        for item in namespaces:
            namespace_id = item["namespace"]
            namespace_id = None if not namespace_id else namespace_id
            namespace_name = item["namespaceShowName"]
            namespace_config_count = item["configCount"]
            p.apply_async(self.download_one_namespace_configs, args=(namespace_id, namespace_name, namespace_config_count, snapshot_base))
        p.close()
        p.join()

    def publish_one_stage_summary(self, stage, publish_for_debug=False):
        """
        Find summary property file and publish to namespace 'summary' if file exist.

        Args:
            stage: stage flag
            publish_for_debug: publish DEBUG summary to group DEBUG if set to True
        """
        logger.debug(f"Handle publishing stage summary properties, stage: {stage}, publish for debug: {publish_for_debug}")
        nacos_client = nacos.NacosClient(self.nacos_server.host, namespace=self.summary_namespace_id)
        self.set_nacos_client_debug(nacos_client)

        summary_group = self.summary_group_debug if publish_for_debug else self.summary_group_stable
        summary_file_name = "+".join([stage, summary_group, self.summary_namespace_id])
        summary_file_path = os.path.join(self.nacos_snapshot_repo_dir, summary_file_name)
        if os.path.exists(summary_file_path):
            logger.debug(f"summary file for stage {stage} exists: {summary_file_path}")
            with open(summary_file_path, "r") as summary:
                content = self.sync_task_reason + "\n\n" + summary.read()
                nacos_client.publish_config(stage, summary_group, content)
                logger.success(f"Succeed to publish summary properties for stage {stage} "
                               f"with content from file {summary_file_name}.")
        else:
            logger.debug(f"summary file for stage {stage} does not exist: {summary_file_path}")

    def collect_and_publish_summary(self, collect_for_debug=False):
        """
        Collect summary properties for stages and publish to namespace 'summary', with data id set to {stage}.

        Args:
            collect_for_debug:  if set to True, summaries for both DEBUG and STAGE group would be published.
        """
        # collect summary for all stages and save to local snapshot base after decoding
        c = Collector(self.nacos_snapshot_repo_dir)
        with tempfile.TemporaryDirectory() as tmp_dir:
            c.generate_all_stages_summary(tmp_dir, collect_for_debug)
            c.encode_properties(tmp_dir, os.path.join(tmp_dir, "nacos.xml"))

        # publish summary property file to Nacos
        threads = len(self.stage_to_namespace_ids.keys())
        if collect_for_debug:
            threads = threads + threads
        p = Pool(threads)
        for stage in self.stage_to_namespace_ids.keys():
            p.apply_async(self.publish_one_stage_summary, args=(stage,))
            if collect_for_debug:
                p.apply_async(self.publish_one_stage_summary, args=(stage, True))
        p.close()
        p.join()

    def add(self, params):
        """
        Add tasks to index (waiting room), just like 'git add .'.

        Args:
            params: parameters got from caller.

        Returns:
            None
        """
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trigger_message = params["content"]
        logger.info(f"{self.sync_trigger_data_id} changed at {date_str}, content: {trigger_message}")
        self.index.append(f"{date_str} | {trigger_message}")

    def clean_index(self):
        """
        Save commits in self.index to file.

        Returns:
            All commit messages (concatenated with "\n").
        """
        # save commit history in self.index to history file
        commit_messages = "\n".join(self.index)
        Path(os.path.dirname(self.commit_history_file)).mkdir(parents=True, exist_ok=True)
        with open(self.commit_history_file, "a", encoding="utf-8") as history_file:
            history_file.write(commit_messages + "\n")
        self.index.clear()
        return commit_messages

    def commit_and_push_to_remote(self, commit_messages):
        """
        Commit and push to git remote repository.
        Args:
            commit_messages: commit messages.

        Returns:
            None
        """
        origin = self.nacos_snapshot_repo.remotes.origin

        if self.nacos_snapshot_repo.is_dirty(untracked_files=True):
            logger.info(f"Changes in local repo {self.nacos_snapshot_repo_dir} found, commit and push starts.")
            logger.debug("add start")
            self.nacos_snapshot_repo.git.add(A=True)
            logger.debug("add end")
            logger.debug("commit start")
            self.nacos_snapshot_repo.index.commit(commit_messages)
            logger.debug("commit end")
            logger.debug("push start")
            info = origin.push()
            # flags of ERROR begins with 1024
            if info[0].flags >= 1024:
                logger.warning(f"Failed to push to remote, "
                               f"summary: {info[0].summary}, flags: {info[0].flags}, commit messages: {commit_messages}"
                               f"try to pull before push.")
                logger.debug("pull start")
                origin.pull()  # pull once before pushing to prevent conflict.
                logger.debug("pull end")
                info_again = origin.push()
                if info_again[0].flags >= 1024:
                    logger.error(f"Failed to push even pulled before,"
                                 f"summary: {info[0].summary}, flags: {info[0].flags}, commit messages: {commit_messages}")
            else:
                logger.success("Push to remote successfully.")
        else:
            logger.warning("One commit was triggered, but current working tree is clean.")

    def dispatch_sync_task(self, params):
        """
        Determine if new sync task can be started.
        Args:
            params: parameter placeholder, set by NacosClient.

        Returns:
            None
        """
        if not self.sync_task_lock:
            self.sync_task_lock = True
            self.sync_to_git(params)
            self.sync_task_lock = False
        else:
            logger.info(f"One sync task (reason: {self.sync_task_reason}) is already running, wait a moment.")

    def sync_to_git(self, params):
        """
        Download all configs from every namespace and sync to git remote.

        Args:
            params: parameters got from caller.

        Returns:
            None
        """
        self.sync_task_reason = self.clean_index()
        logger.info(f"Begin to sync configs from Nacos to git remote, reason: {self.sync_task_reason}")
        self.make_snapshot(self.nacos_snapshot_repo_dir, clean_base=True)
        self.collect_and_publish_summary(collect_for_debug=True)
        self.commit_and_push_to_remote(self.sync_task_reason)
        # Note:
        #   When one watcher is running and then another change occurs, the NacosClient will record the
        #   change but will not call callbacks immediately (call callbacks after last watcher finished instead).
        #   So the IF block below will never run.
        if len(self.index) > 0:
            logger.info(f"Last sync task finished (reason: {self.sync_task_reason}), "
                        f"but index is not empty, begin to sync again.")
            self.sync_to_git(params)
        logger.success(f"Last sync task finished (reason: {self.sync_task_reason}), and index is empty, quit now.")

    def run(self):
        """Trigger sync when nacos.commit.message changes."""
        nacos_client = nacos.NacosClient(self.nacos_server.host)
        self.set_nacos_client_debug(nacos_client)
        nacos_client.set_options(no_snapshot=True)
        nacos_client.add_config_watchers(
            self.sync_trigger_data_id, self.sync_trigger_group, [self.add, self.dispatch_sync_task])
        while True:
            time.sleep(0.1)


class DatabaseSyncer(object):
    """Class representing syncer from database to Nacos."""
    def __init__(self, stage, nacos_server: NacosServer, nacos_client_debug=False):
        """Init an object."""
        self.nacos_server = nacos_server
        self.nacos_client_debug = nacos_client_debug
        self.stage = stage
        assert self.stage in settings.STAGE_TO_NAMESPACE_IDS, \
            f"Stage specified must be one of {settings.STAGE_TO_NAMESPACE_IDS.keys()}"
        self.stage_namespace_id = settings.STAGE_TO_NAMESPACE_IDS[self.stage]

    def set_nacos_client_debug(self, client: nacos.NacosClient):
        """Enable NacosClient debugging when possible."""
        if self.nacos_client_debug:
            client.set_debugging()

    @staticmethod
    def execute_select_statement(connection: pymysql.connections.Connection, sql) -> dict:
        """
        Execute select statement and return result as a dict.

        :param connection: instance of Connection
        :param sql: SQL select statement
        :return: dict of result
        """
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
        logger.debug(f"result: {result}, sql: {sql}")

        return result

    def get_vesync_database_info_from_nacos(self) -> dict:
        """
        Get database info from Nacos.

        :return: dict containing database info
        """
        nacos_client = nacos.NacosClient(self.nacos_server.host, namespace=self.stage_namespace_id)
        self.set_nacos_client_debug(nacos_client)
        configs = nacos_client.get_config(settings.VESYNC_DATABASE_DATA_ID,
                                          settings.VESYNC_DATABASE_GROUP,
                                          no_snapshot=True)
        logger.debug(f"configs (data id: {settings.VESYNC_DATABASE_DATA_ID}, group: {settings.VESYNC_DATABASE_GROUP}): "
                     f"{configs}")
        configs = common.load_properties_from_string(configs)
        database_info = {
            "host": configs[settings.KEY_TO_VESYNC_DATABASE_HOST],
            "port": int(configs[settings.KEY_TO_VESYNC_DATABASE_PORT]),
            "user": configs[settings.KEY_TO_VESYNC_DATABASE_USER],
            "password": configs[settings.KEY_TO_VESYNC_DATABASE_PASSWORD],
            "database": configs[settings.KEY_TO_VESYNC_DATABASE_NAME],
            "charset": "utf8",
            "cursorclass": pymysql.cursors.DictCursor
        }
        logger.info(f"database info used to connect: {database_info}")
        return database_info

    @staticmethod
    def get_vesync_database_connection_pool(database_info: dict) -> ConnectionPool:
        """
        Create database connection and return instance of connection.

        :return: instance of Pool
        """
        connection_pool = ConnectionPool(size=2, name='connection_pool', **database_info)
        return connection_pool

    def get_data_from_table_device_type(self, database_info: dict) -> dict:
        """
        Get info from database table device_type.

        :return: dict containing info from table device_type
        """
        sql = """
            SELECT
                type,
                model,
                model_img,
                model_name,
                device_img,
                config_model,
                detail_table_name,
                device_brand,
                typeV2,
                category
            FROM
                device_type;
        """
        connection = pymysql.connect(**database_info)
        result = self.execute_select_statement(connection, sql)
        device_property_dict = {}
        for item in result:
            key = item["config_model"]
            device_property_dict[key] = item
        logger.debug(f"data from table device_type: {device_property_dict}")
        return device_property_dict

    def get_data_from_table_firmware_info(self, database_info: dict) -> dict:
        """
        Get info from database table firmware_info.

        :return: dict containing info from table firmware_info
        """
        sql = """
            SELECT
                f1.config_module,
                f1.firmware_version,
                f1.device_region,
                f1.firmware_url
            FROM
                firmware_info AS f1
            INNER JOIN (
                SELECT
                    max(version_code) AS max_version_code,
                    config_module,
                    device_region,
                    plugin_name
                FROM
                    firmware_info AS f2
                GROUP BY
                    f2.config_module,
                    f2.device_region,
                    f2.plugin_name ) AS f3 ON
                f1.version_code = f3.max_version_code
                AND f1.config_module = f3.config_module
                AND f1.device_region = f3.device_region
                AND f1.plugin_name = f3.plugin_name;
        """
        connection = pymysql.connect(**database_info)
        result = self.execute_select_statement(connection, sql)
        device_firmware_info_dict = {}
        for item in result:
            key = item["config_module"]
            device_firmware_info_dict[key] = item
        logger.debug(f"data from table firmware_info: {device_firmware_info_dict}")
        return device_firmware_info_dict

    def get_device_type_snapshot_from_nacos(self):
        """
        Get snapshot of table device_type from Nacos.
        """
        nacos_client = nacos.NacosClient(self.nacos_server.host, namespace=self.stage_namespace_id)
        self.set_nacos_client_debug(nacos_client)
        snapshot = nacos_client.get_config(settings.TABLE_DEVICE_TYPE_DATA_ID, settings.DATABASE_SNAPSHOT_GROUP,
                                           no_snapshot=True)
        logger.debug(f"device_type data from Nacos: {snapshot}")
        if snapshot:
            return yaml.safe_load(snapshot)
        else:
            return None

    def get_firmware_info_snapshot_from_nacos(self):
        """
        Get snapshot of table firmware_info from Nacos.
        """
        nacos_client = nacos.NacosClient(self.nacos_server.host, namespace=self.stage_namespace_id)
        self.set_nacos_client_debug(nacos_client)
        snapshot = nacos_client.get_config(settings.TABLE_FIRMWARE_INFO_DATA_ID, settings.DATABASE_SNAPSHOT_GROUP,
                                           no_snapshot=True)
        logger.debug(f"firmware_info data from Nacos: {snapshot}")
        if snapshot:
            return yaml.safe_load(snapshot)
        else:
            return None

    @staticmethod
    def diff_nacos_and_database(data_from_nacos, data_from_database) -> DeepDiff:
        """
        Compare table device_type between data from database and data from Nacos.
        """
        ddiff = DeepDiff(data_from_nacos, data_from_database)
        return ddiff

    def sync_device_type_to_nacos(self, data: dict):
        """
        Publish data from table device_type to Nacos.
        """
        nacos_client = nacos.NacosClient(self.nacos_server.host, namespace=self.stage_namespace_id)
        self.set_nacos_client_debug(nacos_client)
        data = yaml.dump(data)
        logger.debug(f"Update Nacos "
                     f"(data id: {settings.TABLE_DEVICE_TYPE_DATA_ID}, group: {settings.DATABASE_SNAPSHOT_GROUP})"
                     f"with data {data}")
        nacos_client.publish_config(settings.TABLE_DEVICE_TYPE_DATA_ID, settings.DATABASE_SNAPSHOT_GROUP, data)

    def sync_firmware_info_to_nacos(self, data: dict):
        """
        Publish data from table firmware_info to Nacos.
        """
        nacos_client = nacos.NacosClient(self.nacos_server.host, namespace=self.stage_namespace_id)
        self.set_nacos_client_debug(nacos_client)
        data = yaml.dump(data)
        logger.debug(f"Update Nacos "
                     f"(data id: {settings.TABLE_FIRMWARE_INFO_DATA_ID}, group: {settings.DATABASE_SNAPSHOT_GROUP})"
                     f"with data {data}")
        nacos_client.publish_config(settings.TABLE_FIRMWARE_INFO_DATA_ID, settings.DATABASE_SNAPSHOT_GROUP, data)

    def run(self):
        """
        Compare between database and Nacos.
        If any change was detected, sync latest data to Nacos, and send notification via DingTalk.
        """
        access_token = "c8a9d345d0f37a99cf72af8d58a3984409161efa4350c437acf02e31443c90db"
        webhook = f"https://oapi.dingtalk.com/robot/send?access_token={access_token}"
        robot = DingtalkChatbot(webhook)

        database_info = self.get_vesync_database_info_from_nacos()

        while True:
            if self.nacos_server.is_nacos_online():
                is_need_sync_device_type = False
                is_need_sync_firmware_info = False

                try:
                    device_type_from_nacos = self.get_device_type_snapshot_from_nacos()
                    device_type_from_database = self.get_data_from_table_device_type(database_info)
                    firmware_info_from_nacos = self.get_firmware_info_snapshot_from_nacos()
                    firmware_info_from_database = self.get_data_from_table_firmware_info(database_info)
                except NacosRequestException:
                    logger.warning("Something is wrong when trying to get data from nacos, the server may be down.")
                    time.sleep(settings.DATABASE_SYNCER_INTERVAL)
                    continue

                if device_type_from_nacos:
                    ddiff = self.diff_nacos_and_database(device_type_from_nacos, device_type_from_database)
                    if len(ddiff) > 0:
                        robot.send_text(msg=f"DB ({self.stage}) changes on table device_type detected: "
                                            f"{ddiff.pretty()}", is_at_all=True)
                        logger.info("changes on table device_type detected, sync data from database to Nacos")
                        is_need_sync_device_type = True
                    else:
                        logger.info(f"device_type: no changes detected.")
                else:
                    logger.info(f"device_type not found on Nacos, sync data from database to Nacos")
                    is_need_sync_device_type = True

                if is_need_sync_device_type:
                    self.sync_device_type_to_nacos(device_type_from_database)

                if firmware_info_from_nacos:
                    ddiff = self.diff_nacos_and_database(firmware_info_from_nacos, firmware_info_from_database)
                    if len(ddiff) > 0:
                        robot.send_text(msg=f"DB ({self.stage}) changes on table firmware_info detected: "
                                            f"{ddiff.pretty()}", is_at_all=True)
                        logger.info("changes on table firmware_info detected, sync data from database to Nacos")
                        is_need_sync_firmware_info = True
                    else:
                        logger.info(f"firmware_info: no changes detected.")
                else:
                    logger.info(f"firmware_info not found on Nacos, sync data from database to Nacos")
                    is_need_sync_firmware_info = True

                if is_need_sync_firmware_info:
                    self.sync_firmware_info_to_nacos(firmware_info_from_database)

            time.sleep(settings.DATABASE_SYNCER_INTERVAL)
