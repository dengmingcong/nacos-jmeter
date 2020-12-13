from builder import Builder

# b = Builder("debug-fullTest-Core400SUSR-Cloud-API-ci", "../snapshot", "d:\\Program Files (x86)\\jmeter4.0", "test_name_core400susr", "d:\\03 mp products\\01 cg Git代码\\cloud-api-test")
b = Builder("debug-fullTest-Core400SUSR-Alexa-API-ci")
b.generate_new_build_xml("../snapshot", "d:\\Program Files (x86)\\jmeter4.0", "test_name_core400susr", "d:\\03 mp products\\01 cg Git代码\\cloud-api-test", "../test/out.xml")
