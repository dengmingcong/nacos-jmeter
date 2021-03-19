from multiprocessing import Pool
from pathlib import Path
import datetime
import json
import os
import time

from loguru import logger
import git
import nacos
import requests

import settings


class NacosServer(object):
    """Class representing one Nacos server."""
    def __init__(self, host, port):
        """Init class."""
        self.host = host
        self.host_port = f"http://{host}:{port}"
        self.login_path = f"/nacos/#/login"
        self.login_url = f"{self.host_port}{self.login_path}"
        self.get_namespaces_path = f"/nacos/v1/console/namespaces"
        self.get_namespaces_url = f"{self.host_port}{self.get_namespaces_path}"
        assert self._is_nacos_online(), f"Error. Cannot open login page {self.login_url} now."

    def _is_nacos_online(self):
        """Returns true if login url can be opened successfully."""
        logger.info(f"nacos login url: {self.login_url}")
        return requests.get(self.login_url).status_code == 200


class NacosSyncer(object):
    """Class representing syncer from Nacos to git."""
    def __init__(self, nacos_server_host, nacos_server_port, nacos_client_debug=False):
        """Init class."""
        self.nacos_server = NacosServer(nacos_server_host, nacos_server_port)

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
        # get all namespaces information
        response = requests.get(self.nacos_server.get_namespaces_url).text
        logger.info(f"Response of {self.nacos_server.get_namespaces_path}: {response}")
        namespaces = json.loads(response)["data"]
        logger.info("Begin to make snapshot of Nacos.")
        p = Pool(len(namespaces))
        for item in namespaces:
            namespace_id = item["namespace"]
            namespace_id = None if not namespace_id else namespace_id
            namespace_name = item["namespaceShowName"]
            namespace_config_count = item["configCount"]
            p.apply_async(self.download_one_namespace_configs, args=(namespace_id, namespace_name, namespace_config_count, snapshot_base))
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
        with open(self.commit_history_file, "w", encoding="utf-8") as history_file:
            history_file.write(commit_messages)
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
            logger.debug("pull start")
            origin.pull()  # pull once before pushing to prevent conflict.
            logger.debug("pull end")
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
                logger.error(f"Error occurs while pushing to remote, "
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
            try:
                logger.info(f"Begin to sync configs from Nacos to git remote, reason: {self.sync_task_reason}")
                self.make_snapshot(self.nacos_snapshot_repo_dir)
                self.commit_and_push_to_remote(self.sync_task_reason)
                if len(self.index) > 0:
                    logger.info(f"Last sync task finished (reason: {self.sync_task_reason}), "
                                f"but index is not empty, begin to sync again.")
                    self.sync_to_git(params)
            except:
                logger.error(f"Error occurs while doing sync task (reason: {self.sync_task_reason}).")
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


