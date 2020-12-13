from testplan import TestPlan

t = TestPlan("test plan.jmx")
t.change_controller_type()
t.enable_stop_thread()
t.save("test plan new.jmx")