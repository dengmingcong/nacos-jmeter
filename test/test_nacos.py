from nacos import Nacos, Rule

n = Nacos("34.234.176.173", 8848)
n.make_snapshot("../snapshot")
r = Rule(["cross-env", "ci"], ["WiFiBTOnboardingNotify_AirPurifier_LAP-C4004S-WUSR_US"], True)
print(r.apply_to_snapshot("../snapshot"))
