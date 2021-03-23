from multiprocessing import Pool
from pathlib import Path
import datetime
import os
import time
import tempfile

from loguru import logger
import git
import nacos

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
        self.summary_group = settings.SUMMARY_GROUP

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
        logger.info(f"End to get configs from namespace: {namespace_name}")

    def make_snapshot(self, snapshot_base):
        """
        Download all configurations of every namespace to local in parallel.
        Files with the same name will be overwritten.

        :param snapshot_base: Dir to store snapshot config files, whose parent directory is named with 'nacos-snapshot'.
        """
        logger.info("Begin to make snapshot of Nacos.")
        # Note:
        #   When running in Windows, if another change occurs when handling current change, the process will always wait
        #   nearly one minute and I don't know why, but in macOS, it works great.
        #   If running on Linux this happens, log pid to try to find reason.
        p = Pool(len(self.nacos_server.namespaces))
        for item in self.nacos_server.namespaces:
            namespace_id = item["namespace"]
            namespace_id = None if not namespace_id else namespace_id
            namespace_name = item["namespaceShowName"]
            namespace_config_count = item["configCount"]
            p.apply_async(self.download_one_namespace_configs, args=(namespace_id, namespace_name, namespace_config_count, snapshot_base))
        p.close()
        p.join()

    def publish_summary(self):
        """Collect summary properties for stages and publish to public, with data id set to {stage}"""
        c = Collector(self.nacos_snapshot_repo_dir)
        with tempfile.TemporaryDirectory() as tmp_dir:
            c.generate_all_stages_summary(tmp_dir)
            c.encode_properties(tmp_dir, os.path.join(tmp_dir, "nacos.xml"))

        nacos_client = nacos.NacosClient(self.nacos_server.host, namespace=self.summary_namespace_id)
        for stage in self.stage_to_namespace_ids.keys():
            summary_file_name = "+".join([stage, self.summary_group, self.summary_namespace_id])
            summary_file = os.path.join(self.nacos_snapshot_repo_dir, summary_file_name)
            if os.path.exists(summary_file):
                logger.debug(f"summary file for stage {stage} exists: {summary_file}")
                with open(summary_file, "r") as summary:
                    content = self.sync_task_reason + "\n\n" + summary.read()
                    nacos_client.publish_config(stage, self.summary_group, content)
                    logger.debug(f"Succeed to publish summary properties for stage {stage}.")

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
                logger.info("Push to remote successfully.")
        else:
            logger.warning("One commit was triggered, but current working tree is clean.")

    def sync_to_git(self, params):
        """
        Download all configs from every namespace and sync to git remote.

        Args:
            params: parameters got from caller.

        Returns:
            None
        """
        if not self.sync_task_lock:
            self.sync_task_lock = True
            self.sync_task_reason = self.clean_index()
            logger.info(f"Begin to sync configs from Nacos to git remote, reason: {self.sync_task_reason}")
            self.make_snapshot(self.nacos_snapshot_repo_dir)
            self.publish_summary()
            self.commit_and_push_to_remote(self.sync_task_reason)
            # Note:
            #   When one watcher is running and then another change occurs, the NacosClient will record the
            #   change but will not call callbacks immediately (call callbacks after last watcher finished instead).
            #   So the IF block below will never run.
            if len(self.index) > 0:
                logger.info(f"Last sync task finished (reason: {self.sync_task_reason}), "
                            f"but index is not empty, begin to sync again.")
                self.sync_to_git(params)
            self.sync_task_lock = False
            logger.info(f"Last sync task finished (reason: {self.sync_task_reason}), and index is empty, quit now.")
        else:
            logger.info(f"One sync task (reason: {self.sync_task_reason}) is already running, wait a moment.")

    def run(self):
        """Trigger sync when nacos.commit.message changes."""
        nacos_client = nacos.NacosClient(self.nacos_server.host)
        self.set_nacos_client_debug(nacos_client)
        nacos_client.set_options(no_snapshot=True)
        nacos_client.add_config_watchers(self.sync_trigger_data_id, self.sync_trigger_group, [self.add, self.sync_to_git])
        while True:
            time.sleep(0.1)
