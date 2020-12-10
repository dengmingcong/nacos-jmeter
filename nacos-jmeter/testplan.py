import xml.etree.ElementTree as ET


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

    def enable_stop_thread(self):
        """Set on_sample_error to stopthread."""
        thread_groups = self.tree.findall(".//ThreadGroup")
        for thread_group in thread_groups:
            property_on_sampler_error = thread_group.find("stringProp[@name='ThreadGroup.on_sample_error']")
            property_on_sampler_error.text = "stopthread"

    def save(self, out_file):
        """
        Save tree to file.
        :param out_file: file to save as
        """
        self.tree.write(out_file, encoding="utf-8")
