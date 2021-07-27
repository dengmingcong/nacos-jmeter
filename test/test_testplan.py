from testplan import TestPlan

t = TestPlan("SmokeTestCore400SUS.jmx")
t.change_controller_type()
t.add_jsr223listener_to_each_http_request("smokeTest-Core400SUS-Production")
t.save("SmokeTestCore400SUSNew.jmx")