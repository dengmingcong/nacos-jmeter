import os
import settings
import tempfile
import time
from collector import Collector

# b = Builder("debug-fullTest-Core400SUSR-Cloud-API-ci", "../snapshot", "d:\\Program Files (x86)\\jmeter4.0", "test_name_core400susr", "d:\\03 mp products\\01 cg Git代码\\cloud-api-test")
# b = Builder("debug-fullTest-Core400SUSR-Alexa-API-ci")
# b.generate_new_build_xml("../snapshot", "d:\\Program Files (x86)\\jmeter4.0", "test_name_core400susr", "d:\\03 mp products\\01 cg Git代码\\cloud-api-test", "../test/out.xml")

if __name__ == "__main__":
    c = Collector(settings.NACOS_SNAPSHOT_REPO_DIR)
    with tempfile.TemporaryDirectory() as tmp_dir:
        c.generate_all_stages_summary(tmp_dir)
        c.encode_properties(tmp_dir, os.path.join(tmp_dir, "nacos.xml"))
