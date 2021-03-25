from multiprocessing import Pool
from pathlib import Path
import json
import os
import platform
import subprocess
import xml.etree.ElementTree as ET

from loguru import logger

import common
import settings


class Collector(object):
    """Class representing rules describing how to collect configurations from Nacos snapshot."""

    def __init__(self, snapshot_base):
        """
        Init a collector for specified nacos snapshot.

        :param snapshot_base: Dir to store snapshot config files, whose parent directory is named with 'nacos-snapshot'.
        """
        self.snapshot_base = snapshot_base
        assert Path(self.snapshot_base).exists(), f"Error. Directory {self.snapshot_base} does not exist."

        self.cross_env_namespace_id = settings.CROSS_ENV_NAMESPACE_ID
        self.stage_to_namespace_ids = settings.STAGE_TO_NAMESPACE_IDS
        self.summary_namespace_id = settings.SUMMARY_NAMESPACE_ID
        self.debug_group = settings.DEBUG_GROUP
        self.stage_preset_groups = settings.STAGE_PRESET_GROUPS
        self.summary_group_debug = settings.SUMMARY_GROUP_DEBUG
        self.summary_group_stable = settings.SUMMARY_GROUP_STABLE

        # configs after filtered
        self.nacos_snapshot_dict = self._filter_data_ids()

        self.nacos_template_xml = os.path.join(settings.PROJECT_ROOT, "resources", "nacos_template.xml")
        self.extension_before_encode = settings.SUMMARY_EXTENSION_BEFORE_ENCODE
        self.extension_after_encode = settings.SUMMARY_EXTENSION_AFTER_ENCODE

    def _filter_data_ids(self) -> dict:
        """
        Filter config files for preset stages.

        Only config files corresponding to cross-env and stage namespaces retained, other namespaces are omitted.
        Group config files by namespace and group, and save the result to a dict.

        returns as:
            {
                "cross-env": {
                    "SHARED": ["foo", "bar"]
                    "DEVICE": ["foo1"]
                    "DEBUG": ["bar1"]
                }
            }
        """
        # only cross-env and all preset stage namespaces
        target_namespace_ids = [self.cross_env_namespace_id, *list(self.stage_to_namespace_ids.values())]
        target_groups = [*self.stage_preset_groups, self.debug_group]

        # initialize wit empty list
        nacos_snapshot_dict = {}
        for namespace_id in target_namespace_ids:
            nacos_snapshot_dict[namespace_id] = {}
            for group in target_groups:
                nacos_snapshot_dict[namespace_id][group] = []

        for file in os.listdir(self.snapshot_base):
            # filter out files whose names start with "++"
            if not file.startswith("++"):
                parts = file.split("+")
                # keep only files whose name met format as "foo+bar+baz"
                if len(parts) == 3:
                    namespace_id = parts[2]
                    group = parts[1]
                    if namespace_id in target_namespace_ids and group in target_groups:
                        nacos_snapshot_dict[namespace_id][group].append(file)

        logger.debug(f"Config files for all stages after filtering: {json.dumps(nacos_snapshot_dict)}")
        return nacos_snapshot_dict

    def collect(self, stage, debug=False) -> list:
        """
        Collect and return configurations existed in local snapshot for specified stage.
        Each element of the returned list is a config file name, whose format as DATA_ID+GROUP+NAMESPACE

        :param stage: stage flag as ci, testonline, ...
        :param debug: if collecting configs with GROUP set to 'DEBUG'
        :return: list
        """
        valid_stage_flags = self.stage_to_namespace_ids.keys()
        assert stage in valid_stage_flags, f"Stage flag can only be one of {valid_stage_flags}"
        stage_namespace_id = self.stage_to_namespace_ids[stage]
        # cross-env and one specified stage namespace
        target_namespace_ids = [self.cross_env_namespace_id, stage_namespace_id]
        target_groups = self.stage_preset_groups
        if debug:
            target_groups += [self.debug_group]

        product_config_file_list = []
        for namespace_id in target_namespace_ids:
            for group in target_groups:
                data_ids_to_group = self.nacos_snapshot_dict[namespace_id][group]
                if len(data_ids_to_group) > 0:
                    product_config_file_list += data_ids_to_group

        logger.debug(f"Config files collected for stage {stage}: {json.dumps(product_config_file_list)}")
        return product_config_file_list

    def _generate_one_stage_summary(self, stage, dst_dir, debug=False):
        """
        Generate a property file by concatenating all configs for the specific stage.

        The extension will be set to ".utf8" temporarily for later encoding.
        The group will be set to DEBUG if parameter debug was set True, else to STABLE.

        Args:
            stage: stage flag as ci, testonline, ...
            dst_dir: dir to store file generated
            debug: if set True, data ids with group "DEBUG" will be collected too
        """
        summary_group = self.summary_group_debug if debug else self.summary_group_stable
        summary_file_name = "+".join([stage, summary_group, self.summary_namespace_id]) + \
                            self.extension_before_encode
        config_file_list = self.collect(stage, debug)
        absolute_path_config_file_list = list(map(lambda x: os.path.join(self.snapshot_base, x), config_file_list))
        summary_file_path = os.path.join(dst_dir, summary_file_name)
        common.concatenate_files(absolute_path_config_file_list, summary_file_path)

    def generate_all_stages_summary(self, dst_dir, collect_for_debug=False):
        """
        Generate summary property file for each stage.

        Args:
            dst_dir: dir to store file generated
            collect_for_debug: if set to True, collect for both STABLE and DEBUG, else for only STABLE
        """
        threads = len(self.stage_to_namespace_ids.keys())
        if collect_for_debug:
            threads = threads + threads
        p = Pool(threads)
        for stage in self.stage_to_namespace_ids.keys():
            p.apply_async(self._generate_one_stage_summary, args=(stage, dst_dir))
            if collect_for_debug:
                p.apply_async(self._generate_one_stage_summary, args=(stage, dst_dir, True))
        p.close()
        p.join()

    def encode_properties(self, src_dir, out_build_xml):
        """
        Encode all files with extension ".utf8" and move new files to self.snapshot_base.

        Steps:
            1. Go to src_dir, find all files with extension ".utf8"
            2. Encode these files and generate new files with extension ".properties"
            3. Move all files with extension ".properties" to self.snapshot and remove the extension.
        Args:
            src_dir: directory stores the property files with extension ".utf8"
            out_build_xml: new ant build.xml

        Returns:
            None
        """
        tree = ET.parse(self.nacos_template_xml)

        project_root_element = tree.getroot()
        ant_task_move_element = tree.find(".//move")

        project_root_element.set("basedir", src_dir)
        ant_task_move_element.set("todir", self.snapshot_base)

        tree.write(out_build_xml, encoding="utf-8")
        logger.success(f"build.xml for decode properties generated: {out_build_xml}")
        if platform.system() == "Windows":
            build_xml_dir = os.path.dirname(out_build_xml)
            build_xml_file_name = os.path.basename(out_build_xml)
            os.chdir(build_xml_dir)
            subprocess.run(f"ant -f {build_xml_file_name}", shell=True)
            os.chdir(self.snapshot_base)
        else:
            subprocess.run(["ant", "-f", out_build_xml])
        logger.success(f"succeed to decode properties.")
