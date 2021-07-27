from loguru import logger
from lxml import etree as ET


class TestPlan(object):
    """Class representing a JMeter test plan (jmx)."""
    def __init__(self, test_plan):
        """
        Init a test plan.

        :param test_plan: full path of a JMeter jmx
        """
        self.test_plan = test_plan
        self.tree = ET.parse(self.test_plan)

    def change_controller_type(self):
        """Convert simple controller to transaction controller."""
        simple_controllers = self.tree.findall(".//GenericController")
        for simple_controller in simple_controllers:
            # change tag
            simple_controller.tag = "TransactionController"
            # set attributes "guiclass", "testclass".
            simple_controller.set("guiclass", "TransactionControllerGui")
            simple_controller.set("testclass", "TransactionController")
            # add two sub-elements
            property_timer = ET.SubElement(simple_controller, "boolProp", attrib={"name": "TransactionController.includeTimers"})
            property_timer.text = "false"
            property_parent = ET.SubElement(simple_controller, "boolProp", attrib={"name": "TransactionController.parent"})
            property_parent.text = "true"

        # set all transaction controllers generating parent sample.
        transaction_controllers = self.tree.findall(".//TransactionController")
        for transaction_controller in transaction_controllers:
            property_parent = transaction_controller.find("boolProp[@name='TransactionController.parent']")
            property_parent.text = "true"

    def add_jsr223listener_to_each_http_request(self, jenkins_job_name):
        """Add JSR223Listener Sub-Element to each http request element to support open falcon."""
        jmeter_test_plan = self.tree.getroot()

        if jmeter_test_plan.get("monitored"):
            logger.debug("JSR223Listener has added to every HTTP Request Sampler, skip")
            return
        else:
            jmeter_test_plan.set("monitored", "true")

        hash_trees = self.tree.xpath(".//HTTPSamplerProxy/following-sibling::hashTree[1]")

        for hash_tree in hash_trees:
            # fist http requests is preheat interface, no need to upload monitoring
            if hash_trees.index(hash_tree) == 0:
                continue

            # add one sub-elements
            jsr223_tree = ET.SubElement(hash_tree, "JSR223Listener")

            # set attributes "guiclass", "testclass", "testname", "enabled".
            jsr223_tree.set("guiclass", "TestBeanGUI")
            jsr223_tree.set("testclass", "JSR223Listener")
            jsr223_tree.set("testname", "JSR223 Listener")
            jsr223_tree.set("enabled", "true")

            # add 4 sub-elements
            script_language = ET.SubElement(jsr223_tree, "stringProp", attrib={"name": "scriptLanguage"})
            script_language.text = "groovy"

            filename = ET.SubElement(jsr223_tree, "stringProp", attrib={"name": "filename"})
            filename.text = "pushToFalcon.groovy"

            parameters = ET.SubElement(jsr223_tree, "stringProp", attrib={"name": "parameters"})
            parameters.text = jenkins_job_name

            cache_key = ET.SubElement(jsr223_tree, "stringProp", attrib={"name": "cacheKey"})
            cache_key.text = "true"

    def set_on_sample_error(self, value):
        """Set on_sample_error."""
        if value not in ["continue", "stopthread"]:
            raise ValueError("can only be set to 'continue' or 'stopthread'")
        thread_groups = self.tree.findall(".//ThreadGroup")
        for thread_group in thread_groups:
            property_on_sampler_error = thread_group.find("stringProp[@name='ThreadGroup.on_sample_error']")
            property_on_sampler_error.text = value

    def save(self, out_file):
        """
        Save tree to file.
        :param out_file: file to save as
        """
        self.tree.write(out_file, encoding="utf-8", xml_declaration=True, pretty_print=True)
